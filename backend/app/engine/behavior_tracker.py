"""游戏行为追踪器：分析每一步决策并立即写入 SQLite。"""

import json
from collections import Counter
from datetime import datetime
from time import perf_counter
from typing import Dict, List, Optional

from .ai_player import RuleAIPlayer
from .card import Card
from .card_type import BOMB, JOKER_BOMB, STRAIGHT_FLUSH, identify_card_type
from .game import Game
from .turn import Turn
from ..database.sqlite import (
    BehaviorLog,
    create_behavior_log,
    create_game_record,
    update_game_record,
)


BOMB_TYPES = {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}


class BehaviorTracker:
    """围绕现有 Game 自动记录决策行为，不改变游戏对象接口。"""

    def __init__(self, game: Game, game_record_id: Optional[int] = None) -> None:
        self.game = game
        if game_record_id is None:
            record = create_game_record(game.to_dict())
            self.game_record_id = record.id
        else:
            self.game_record_id = game_record_id
        self.pass_count = 0
        self.bomb_use_count = 0
        self.recommendation_click_count = 0

    @staticmethod
    def _count_retained_bombs(hand: List[Card]) -> int:
        """统计手牌中仍完整保留的同点数四张以上炸弹数量。"""
        value_counts = Counter(card.value for card in hand)
        normal_bombs = sum(1 for count in value_counts.values() if count >= 4)
        joker_counts = sorted(
            Counter(card.value for card in hand if card.is_joker).values()
        )
        joker_bomb = int(joker_counts == [2, 2])
        return normal_bombs + joker_bomb

    @staticmethod
    def _did_split_cards(hand_before: List[Card], played_cards: List[Card]) -> bool:
        """判断是否从对子、三张或炸弹中只取出部分同点数牌。

        这是可解释且稳定的拆牌定义：某点数原本至少有两张，当前只打出其中一部分，
        并在手中留下相同点数牌，即视为拆牌。
        """
        before_counts = Counter(card.value for card in hand_before)
        played_counts = Counter(card.value for card in played_cards)
        return any(
            before_counts[value] >= 2 and 0 < count < before_counts[value]
            for value, count in played_counts.items()
        )

    def _helped_partner(self, turn: Turn, previous_player) -> bool:
        """队友掌握牌权时选择 PASS，记为帮助队友保持主动权。"""
        return bool(
            turn.is_pass
            and previous_player is not None
            and previous_player is not turn.player
            and previous_player.team_id == turn.player.team_id
        )

    def _is_critical_decision(self, turn: Turn, bomb_used: bool) -> bool:
        """炸弹、本人残局或任一对手进入五张以内时标记为关键决策。"""
        player_endgame = len(turn.player.hand) <= 8
        opponent_endgame = any(
            player.team_id != turn.player.team_id and len(player.hand) <= 5
            for player in self.game.players
        )
        return bomb_used or player_endgame or opponent_endgame

    def record_recommendation_click(self, player_name: str) -> BehaviorLog:
        """记录一次 AI 建议点击并立即写入数据库。"""
        self.recommendation_click_count += 1
        return create_behavior_log(
            self.game_record_id,
            player_name,
            "recommendation_click",
            {"total_clicks": self.recommendation_click_count},
        )

    def execute_ai_turn(
        self,
        ai: RuleAIPlayer,
        recommendation_clicked: bool = False,
    ) -> BehaviorLog:
        """执行一个 AI 回合，自动分析并持久化全部行为指标。

        思考时间从规则 AI 开始决策到 Turn 返回为止。数据库写入发生在动作完成后，
        因而计时不包含 SQLite 提交耗时，更接近真实决策耗时。
        """
        round_obj = self.game.current_round
        if round_obj is None:
            raise ValueError("Game 尚未开始，无法记录行为")
        previous_player = round_obj.last_player
        hand_before = list(ai.player.hand)

        if recommendation_clicked:
            self.record_recommendation_click(ai.player.name)

        started = perf_counter()
        turn = ai.play()
        thinking_time_ms = (perf_counter() - started) * 1000

        card_type = identify_card_type(turn.cards)
        bomb_used = card_type["type"] in BOMB_TYPES
        if turn.is_pass:
            self.pass_count += 1
        if bomb_used:
            self.bomb_use_count += 1

        detail: Dict[str, object] = {
            "thinking_time_ms": round(thinking_time_ms, 3),
            "passed": turn.is_pass,
            "pass_count": self.pass_count,
            "bomb_used": bomb_used,
            "bomb_use_count": self.bomb_use_count,
            "bombs_retained": self._count_retained_bombs(ai.player.hand),
            "helped_partner": self._helped_partner(turn, previous_player),
            "split_cards": self._did_split_cards(hand_before, turn.cards),
            "recommendation_clicked": recommendation_clicked,
            "recommendation_click_count": self.recommendation_click_count,
            "critical_decision": self._is_critical_decision(turn, bomb_used),
            "card_type": card_type,
            "turn": turn.to_dict(),
        }
        return create_behavior_log(
            self.game_record_id,
            ai.player.name,
            "game_step",
            detail,
        )

    def finish_game(self) -> None:
        """在牌局结束时把胜者和最终状态写回游戏记录。"""
        update_game_record(
            self.game_record_id,
            state=self.game.to_dict(),
            winner=self.game.winner.name if self.game.winner else None,
            ended_at=datetime.utcnow(),
        )

    @staticmethod
    def detail(log: BehaviorLog) -> Dict[str, object]:
        """把 BehaviorLog 的 JSON 文本还原为字典，便于统计和展示。"""
        return json.loads(log.detail_json)


__all__ = ["BehaviorTracker"]
