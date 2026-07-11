"""根据 BehaviorLog 自动累计五维评分并映射七种人格。"""

import json
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from sqlalchemy import select

from .personality_weights import (
    BASE_SCORES,
    DIMENSIONS,
    EVENT_WEIGHTS,
    PERSONALITY_RULES,
    THINKING_THRESHOLDS,
)
from ..database.sqlite import (
    BehaviorLog,
    PersonalityScore,
    SessionLocal,
    create_personality_score,
)


ScoreResult = Dict[str, float]


class PersonalityScoringEngine:
    """可增量使用的人格评分器，权重可在构造时整体替换。"""

    def __init__(
        self,
        base_scores: Optional[Mapping[str, float]] = None,
        event_weights: Optional[Mapping[str, Mapping[str, float]]] = None,
        thinking_thresholds: Optional[Mapping[str, float]] = None,
    ) -> None:
        self.base_scores = dict(base_scores or BASE_SCORES)
        self.event_weights = {
            event: dict(weights)
            for event, weights in (event_weights or EVENT_WEIGHTS).items()
        }
        self.thinking_thresholds = dict(thinking_thresholds or THINKING_THRESHOLDS)
        self.scores: ScoreResult = {
            dimension: float(self.base_scores.get(dimension, 50.0))
            for dimension in DIMENSIONS
        }

    @staticmethod
    def _clamp(value: float) -> float:
        """保证任何维度始终位于 0～100。"""
        return max(0.0, min(100.0, value))

    def reset(self) -> None:
        """恢复全部维度的配置基准分。"""
        self.scores = {
            dimension: float(self.base_scores.get(dimension, 50.0))
            for dimension in DIMENSIONS
        }

    def _apply_event(self, event: str) -> None:
        """应用一个配置事件，并在每次累计后立即限制范围。"""
        for dimension, delta in self.event_weights.get(event, {}).items():
            if dimension in self.scores:
                self.scores[dimension] = self._clamp(self.scores[dimension] + delta)

    def _events_from_detail(self, detail: Mapping[str, object]) -> List[str]:
        """把 BehaviorTracker 的明细转换为独立权重事件。"""
        events: List[str] = []
        passed = bool(detail.get("passed", False))
        bomb_used = bool(detail.get("bomb_used", False))
        critical = bool(detail.get("critical_decision", False))
        thinking_time = float(detail.get("thinking_time_ms", 0.0) or 0.0)

        if passed:
            events.append("pass")
        if bomb_used:
            events.append("bomb_used")
        if bomb_used and critical:
            events.append("critical_bomb")
        if int(detail.get("bombs_retained", 0) or 0) > 0:
            events.append("bomb_retained")
        if bool(detail.get("helped_partner", False)):
            events.append("helped_partner")
        if bool(detail.get("split_cards", False)):
            events.append("split_cards")
        # 建议点击已有独立 recommendation_click 日志，此处不重复累计步骤中的标记。

        if thinking_time > self.thinking_thresholds["slow"]:
            events.append("slow_thinking")
        else:
            events.append("normal_decision")
        if thinking_time > self.thinking_thresholds["very_slow"]:
            events.append("very_slow_thinking")
        if critical and thinking_time <= self.thinking_thresholds["fast_critical"]:
            events.append("fast_critical_decision")
        return events

    def add_log(self, log: BehaviorLog) -> ScoreResult:
        """累计一条 BehaviorLog，并返回当前五维结果。"""
        if log.behavior_type == "recommendation_click":
            self._apply_event("recommendation_click")
            return self.result()
        if log.behavior_type != "game_step":
            return self.result()
        try:
            detail = json.loads(log.detail_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f"BehaviorLog {log.id} 的 detail_json 无效") from exc
        if not isinstance(detail, dict):
            raise ValueError(f"BehaviorLog {log.id} 的 detail_json 必须是对象")
        for event in self._events_from_detail(detail):
            self._apply_event(event)
        return self.result()

    def score_logs(self, logs: Iterable[BehaviorLog], reset: bool = True) -> ScoreResult:
        """按日志顺序累计；默认先重置，避免重复调用造成重复计分。"""
        if reset:
            self.reset()
        for log in logs:
            self.add_log(log)
        return self.result()

    def score_game(self, game_record_id: int) -> ScoreResult:
        """从 SQLite 读取指定牌局的所有行为日志并自动评分。"""
        with SessionLocal() as session:
            statement = (
                select(BehaviorLog)
                .where(BehaviorLog.game_record_id == game_record_id)
                .order_by(BehaviorLog.id.asc())
            )
            logs = list(session.scalars(statement))
        return self.score_logs(logs)

    def score_player(
        self,
        player_name: str,
        game_record_id: Optional[int] = None,
    ) -> ScoreResult:
        """从 SQLite 累计某玩家的日志，可选择限定单局。"""
        with SessionLocal() as session:
            statement = select(BehaviorLog).where(BehaviorLog.player_name == player_name)
            if game_record_id is not None:
                statement = statement.where(BehaviorLog.game_record_id == game_record_id)
            statement = statement.order_by(BehaviorLog.id.asc())
            logs = list(session.scalars(statement))
        return self.score_logs(logs)

    def result(self) -> ScoreResult:
        """按固定字段输出五维分数。"""
        return {
            "attack": round(self.scores["attack"], 2),
            "cooperation": round(self.scores["cooperation"], 2),
            "risk": round(self.scores["risk"], 2),
            "hesitation": round(self.scores["hesitation"], 2),
            "emotion": round(self.scores["emotion"], 2),
        }

    @staticmethod
    def _matches(scores: Mapping[str, float], conditions: List[Tuple[str, str, float]]) -> bool:
        """执行人格配置中的简单阈值条件。"""
        for dimension, operator, threshold in conditions:
            value = scores[dimension]
            if operator == ">=" and value < threshold:
                return False
            if operator == "<=" and value > threshold:
                return False
            if operator not in {">=", "<="}:
                raise ValueError(f"不支持的人格比较符: {operator}")
        return True

    def personality(self, scores: Optional[Mapping[str, float]] = None) -> str:
        """把五维分数自动映射为七种人格之一。"""
        current_scores = scores or self.result()
        for name, conditions in PERSONALITY_RULES:
            if self._matches(current_scores, conditions):
                return name
        return "均衡稳健型"

    def score_and_save(
        self,
        player_name: str,
        game_record_id: Optional[int] = None,
    ) -> PersonalityScore:
        """评分后写入现有 personality_score 表并返回 ORM 记录。"""
        scores = self.score_player(player_name, game_record_id)
        return create_personality_score(
            player_name=player_name,
            aggressive_score=scores["attack"],
            balanced_score=(scores["cooperation"] + scores["emotion"]) / 2,
            conservative_score=100.0 - scores["risk"],
            game_record_id=game_record_id,
        )


__all__ = ["PersonalityScoringEngine", "ScoreResult"]
