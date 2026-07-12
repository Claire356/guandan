"""根据 BehaviorLog 自动累计五维评分并映射七种人格。"""

import json
from statistics import pvariance
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
from .weight_config import (
    BASE_SCORE as PROFILE_BASE_SCORE,
    COMPONENT_WEIGHTS,
    DIMENSIONS as PROFILE_DIMENSIONS,
    EVENT_WEIGHTS as PROFILE_EVENT_WEIGHTS,
    EXPLANATIONS,
    LABELS,
    PERSONALITY_BOUNDARY,
    SCORE_MAX,
    SCORE_MIN,
    TIME_THRESHOLDS_MS,
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

    @staticmethod
    def percentile_rank(value: float, all_values: Iterable[float]) -> float:
        """计算 0～1 百分位；没有总体样本时返回中性 0.5。"""
        values = list(all_values)
        if not values:
            return 0.5
        return sum(candidate <= value for candidate in values) / len(values)

    @staticmethod
    def _assemble_profile(components: Mapping[str, Mapping[str, float]]) -> Dict[str, object]:
        """按配置权重把组件分数组装成最终报告。"""
        scores = {}
        for dimension, values in components.items():
            weighted = sum(values[name] * weight for name, weight in COMPONENT_WEIGHTS[dimension].items())
            value = weighted if dimension == "decision" else 50 + (weighted - 50) * 0.8
            scores[dimension] = max(SCORE_MIN, min(SCORE_MAX, value))
        rounded = {key: round(value, 2) for key, value in scores.items()}
        tags = [
            LABELS[dimension]["high" if rounded[dimension] > PERSONALITY_BOUNDARY else "low"]
            for dimension in PROFILE_DIMENSIONS
        ]
        return {
            "scores": rounded,
            "tags": tags,
            "dimensions": [
                {
                    "key": dimension,
                    "score": rounded[dimension],
                    "tag": tag,
                    "explanation": EXPLANATIONS[tag],
                    "components": {name: round(value, 2) for name, value in components[dimension].items()},
                }
                for dimension, tag in zip(PROFILE_DIMENSIONS, tags)
            ],
            "overall_score": round(sum(rounded.values()) / len(rounded), 1),
        }

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
        profile = self.profile_for_player(player_name, game_record_id)
        return create_personality_score(
            player_name=player_name,
            aggressive_score=scores["attack"],
            balanced_score=(scores["cooperation"] + scores["emotion"]) / 2,
            conservative_score=100.0 - scores["risk"],
            game_record_id=game_record_id,
            aggression_score=profile["scores"]["aggression"],
            cooperation_score=profile["scores"]["cooperation"],
            emotion_score=profile["scores"]["emotion"],
            risk_score=profile["scores"]["risk"],
            decision_score=profile["scores"]["decision"],
            personality_tags="|".join(profile["tags"]),
        )

    @staticmethod
    def _profile_events(detail: Mapping[str, object]) -> List[str]:
        """把行为日志转换为新版五维画像事件，字段缺失时保持中性。"""
        events: List[str] = []
        thinking_time = float(detail.get("thinking_time_ms", 0.0) or 0.0)
        direct_flags = {
            "bomb_used": "bomb_used",
            "control_contested": "control_contested",
            "active_attack": "active_attack",
            "played_over_partner": "played_over_partner",
            "protected_partner": "protected_partner",
            "feed_succeeded": "feed_succeeded",
            "split_bomb_for_partner": "split_bomb_for_partner",
            "yielded_control": "yielded_control",
            "speed_changed_after_loss": "speed_changed_after_loss",
            "speed_changed_after_win": "speed_changed_after_win",
            "high_decision_variance": "high_decision_variance",
            "critical_play_fluctuation": "critical_play_fluctuation",
            "early_big_card": "early_big_card",
            "late_small_card": "late_small_card",
            "high_card_used": "high_card_used",
            "risky_play": "risky_play",
            "rapid_streak": "rapid_streak",
        }
        for field, event in direct_flags.items():
            if bool(detail.get(field, False)):
                events.append(event)
        if bool(detail.get("bomb_used", False)) and bool(detail.get("critical_decision", False)):
            events.append("critical_bomb")
        if bool(detail.get("helped_partner", False)) or (
            bool(detail.get("passed", False)) and bool(detail.get("partner_has_control", False))
        ):
            events.append("partner_pass")
        if bool(detail.get("split_cards", False)):
            events.append("split_cards")
        if thinking_time and thinking_time <= TIME_THRESHOLDS_MS["decisive"]:
            events.append("decision_under_4s")
        if thinking_time > TIME_THRESHOLDS_MS["slow"]:
            events.append("slow_decision")
        if bool(detail.get("critical_decision", False)) and thinking_time <= TIME_THRESHOLDS_MS["critical_fast"]:
            events.append("fast_critical_decision")
        return events

    def profile_logs(self, logs: Iterable[BehaviorLog]) -> Dict[str, object]:
        """按附件比例聚合五维画像；没有样本时所有维度保持 50 分。"""
        details = []
        for log in logs:
            if log.behavior_type != "game_step":
                continue
            try:
                detail = json.loads(log.detail_json)
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(detail, dict):
                details.append(detail)

        if not details:
            components = {dimension: {} for dimension in PROFILE_DIMENSIONS}
            # 无样本时明确返回五个 50 分，避免空组件参与加权。
            return {
                "scores": {dimension: PROFILE_BASE_SCORE for dimension in PROFILE_DIMENSIONS},
                "tags": [LABELS[dimension]["low"] for dimension in PROFILE_DIMENSIONS],
                "dimensions": [
                    {"key": dimension, "score": PROFILE_BASE_SCORE, "tag": LABELS[dimension]["low"],
                     "explanation": EXPLANATIONS[LABELS[dimension]["low"]], "components": {}}
                    for dimension in PROFILE_DIMENSIONS
                ],
                "overall_score": PROFILE_BASE_SCORE,
            }
        else:
            total = len(details)
            times = [float(item.get("thinking_time_ms", 0.0) or 0.0) / 1000 for item in details]
            ratio = lambda field: sum(bool(item.get(field, False)) for item in details) / total * 100
            bomb_rate = ratio("bomb_used")
            quick_ratio = sum(value < 4 for value in times) / total * 100
            components = {
                "aggression": {
                    "bomb_frequency": bomb_rate,
                    "override_partner": ratio("played_over_partner"),
                    "play_speed": quick_ratio,
                    "power_struggle": ratio("control_contested") or ratio("active_attack"),
                },
                "cooperation": {
                    "protect_partner": ratio("protected_partner"),
                    "let_partner_play": ratio("helped_partner") or ratio("yielded_control"),
                    "feed_success": ratio("feed_succeeded"),
                    "break_bomb_for_partner": ratio("split_bomb_for_partner"),
                },
                "emotion": {
                    "loss_impact": ratio("speed_changed_after_loss"),
                    "win_impact": ratio("speed_changed_after_win"),
                    "speed_variance": min(100.0, pvariance(times) * 10 if len(times) > 1 else 0.0),
                },
                "risk": {
                    "bomb_frequency": bomb_rate,
                    "risky_big_cards": ratio("early_big_card") or ratio("risky_play"),
                    "risky_small_cards": ratio("late_small_card"),
                    "big_card_frequency": ratio("high_card_used"),
                    "break_combinations": ratio("split_cards"),
                },
                "decision": {"quick_decision_ratio": quick_ratio},
            }
        return self._assemble_profile(components)

    def profile_for_player(
        self,
        player_name: str,
        game_record_id: Optional[int] = None,
    ) -> Dict[str, object]:
        """从 SQLite 读取指定玩家行为并生成新版人格报告。"""
        with SessionLocal() as session:
            statement = select(BehaviorLog).where(BehaviorLog.behavior_type == "game_step")
            if game_record_id is not None:
                statement = statement.where(BehaviorLog.game_record_id == game_record_id)
            all_logs = list(session.scalars(statement.order_by(BehaviorLog.id.asc())))
        grouped: Dict[str, List[BehaviorLog]] = {}
        for log in all_logs:
            grouped.setdefault(log.player_name, []).append(log)
        target = self.profile_logs(grouped.get(player_name, []))
        population = [self.profile_logs(items) for items in grouped.values()]
        if len(population) < 2 or not target["dimensions"]:
            return target
        percentile_components: Dict[str, Dict[str, float]] = {}
        for dimension in target["dimensions"]:
            key = dimension["key"]
            percentile_components[key] = {}
            for component, value in dimension["components"].items():
                peers = [
                    next(item for item in report["dimensions"] if item["key"] == key)["components"].get(component, 0.0)
                    for report in population
                ]
                percentile_components[key][component] = self.percentile_rank(value, peers) * 100
        return self._assemble_profile(percentile_components)


__all__ = ["PersonalityScoringEngine", "ScoreResult"]
