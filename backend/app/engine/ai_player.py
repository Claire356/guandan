"""可直接接入 Game 的规则型掼蛋 AI。"""

import logging
from typing import Dict, List, Optional

from .card import Card
from .card_type import (
    BOMB,
    JOKER_BOMB,
    STRAIGHT_FLUSH,
    CardTypeResult,
    identify_card_type,
    is_wild_card,
)
from .game import Game
from .player import Player
from .turn import Turn
from .move_generator import get_all_legal_moves
from .validator import validate_play


BOMB_TYPES = {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}
logger = logging.getLogger(__name__)


class RuleAIPlayer:
    """三种规则策略共用的候选生成与出牌流程。"""

    style = "rule"

    def __init__(self, game: Game, player: Player) -> None:
        self.game = game
        self.player = player
        self.last_legal_moves: List[List[Card]] = []
        self.last_evaluations: List[Dict[str, object]] = []

    def _current_card_type(self) -> Optional[CardTypeResult]:
        """从当前 Game 中读取桌面牌型；新一轮主动出牌时返回 None。"""
        round_obj = self.game.current_round
        if round_obj is None or round_obj.last_played_cards is None:
            return None
        return round_obj.last_card_type or identify_card_type(round_obj.last_played_cards, self.game.state.current_level)

    def _legal_candidates(self, current_card_type: Optional[CardTypeResult]) -> List[List[Card]]:
        """AI唯一合法动作来源：统一验证器get_all_legal_moves。"""
        self.last_legal_moves = get_all_legal_moves(self.player.hand, current_card_type, self.game.state.current_level)
        return self.last_legal_moves

    def _partner_has_control(self) -> bool:
        """判断当前桌面最后出牌者是否为自己的对家队友。"""
        round_obj = self.game.current_round
        return bool(
            round_obj
            and round_obj.last_player
            and round_obj.last_player is not self.player
            and round_obj.last_player.team_id == self.player.team_id
        )

    def _style_adjustment(
        self,
        cards: List[Card],
        card_type: Optional[CardTypeResult],
        current_card_type: Optional[CardTypeResult],
    ) -> float:
        """子类只调整策略偏好，不参与合法动作生成。"""
        return 0.0

    def evaluate(
        self,
        cards: List[Card],
        current_card_type: Optional[CardTypeResult] = None,
    ) -> Dict[str, float]:
        """第三层：对一个已合法动作计算EV、保炸、协作、残局和风险价值。"""
        if not any(cards == move for move in self.last_legal_moves):
            raise ValueError("evaluate只能评估get_all_legal_moves返回的动作")
        is_pass = not cards
        card_type = None if is_pass else identify_card_type(cards, self.game.state.current_level)
        is_bomb = bool(card_type and card_type["type"] in BOMB_TYPES)
        partner_control = self._partner_has_control()
        hand_size = max(1, len(self.player.hand))
        endgame = hand_size <= 8

        shedding_value = 0.0 if is_pass else len(cards) / hand_size
        bomb_retention_value = 0.2 if not is_bomb else (-0.05 if current_card_type and current_card_type["type"] in BOMB_TYPES else -0.3)
        cooperation_value = 0.45 if partner_control and is_pass else (-0.45 if partner_control and len(cards) != hand_size else 0.0)
        endgame_value = (0.45 * shedding_value if endgame else 0.0) + (-0.2 if endgame and is_pass and not partner_control else 0.0)
        level = 0 if card_type is None else float(card_type["level"])
        risk_value = 0.0 if is_pass else -(level / 170.0) - (0.12 if is_bomb else 0.0)
        style_value = self._style_adjustment(cards, card_type, current_card_type)
        expected_value = shedding_value + bomb_retention_value + cooperation_value + endgame_value + risk_value + style_value
        return {
            "expected_value": round(expected_value, 4),
            "bomb_retention_value": round(bomb_retention_value, 4),
            "cooperation_value": round(cooperation_value, 4),
            "endgame_value": round(endgame_value, 4),
            "risk_value": round(risk_value, 4),
        }

    def recommend(self, current_card_type: Optional[CardTypeResult] = None) -> List[Card]:
        """推荐一组牌；没有可压制的牌时返回空列表表示过牌。"""
        if current_card_type is None:
            current_card_type = self._current_card_type()
        legal_moves = self._legal_candidates(current_card_type)
        if not legal_moves:
            raise RuntimeError("拥有主动出牌权时必须至少存在一个合法动作")
        self.last_evaluations = [
            {"cards": cards, "score": self.evaluate(cards, current_card_type)}
            for cards in legal_moves
        ]
        best_item = max(self.last_evaluations, key=lambda item: item["score"]["expected_value"])
        recommendation = best_item["cards"]

        # 第四层硬约束：推荐必须原样来自第二层合法动作集合。
        assert any(recommendation == move for move in legal_moves), "AI推荐不在Legal Moves中"
        if recommendation:
            validation = validate_play(self.player.hand, current_card_type, recommendation, self.game.state.current_level)
            assert validation["valid"], f"Legal Move最终校验失败: {validation['reason']}"
        else:
            assert current_card_type is not None, "拥有主动出牌权时不能PASS"
        logger.debug("合法动作=%s AI评分=%s 最终推荐=%s", legal_moves, self.last_evaluations, recommendation or "PASS")
        return recommendation

    def recommend_with_reason(self) -> dict:
        """输出可解释推荐，同时兼顾队友、炸弹、牌权、残局、级牌与逢人配。"""
        current_type = self._current_card_type()
        cards = self.recommend(current_type)
        if not cards:
            partner_control = self._partner_has_control() if hasattr(self, "_partner_has_control") else False
            reason = "队友掌握牌权，选择PASS保留牌力" if partner_control else "没有能够合法压过当前牌型的组合，选择PASS"
            evaluation = next(item["score"] for item in self.last_evaluations if item["cards"] == [])
            return {"recommend_cards": [], "reason": reason, "expected_value": evaluation["expected_value"]}

        card_type = identify_card_type(cards, self.game.state.current_level)
        is_bomb = card_type["type"] in BOMB_TYPES
        uses_wild = any(is_wild_card(card, self.game.state.current_level) for card in cards)
        endgame = len(self.player.hand) <= 8
        reasons = []
        if current_type is not None:
            reasons.append("用可控成本压过当前牌型并争取牌权")
        else:
            reasons.append("主动出牌并优先减少手牌张数")
        if is_bomb:
            reasons.append("当前收益足以使用炸弹" if endgame or current_type and current_type["type"] in BOMB_TYPES else "该炸弹能直接取得牌权")
        else:
            reasons.append("保留炸弹用于关键轮次")
        if uses_wild:
            reasons.append(f"利用红桃{self.game.state.current_level}逢人配组成更大合法牌型")
        if endgame:
            reasons.append("已进入残局，优先控制牌权和加速走牌")
        evaluation = next(item["score"] for item in self.last_evaluations if item["cards"] == cards)
        return {"recommend_cards": cards, "reason": "；".join(reasons), "expected_value": evaluation["expected_value"]}

    def chooseBomb(self, current_card_type: Optional[CardTypeResult] = None) -> List[Card]:
        """选择当前能出的最合适炸弹；不存在时返回空列表。"""
        if current_card_type is None:
            current_card_type = self._current_card_type()
        bombs = [
            cards
            for cards in self._legal_candidates(current_card_type)
            if cards and identify_card_type(cards, self.game.state.current_level)["type"] in BOMB_TYPES
        ]
        if not bombs:
            return []
        return max(bombs, key=lambda cards: self.evaluate(cards, current_card_type)["expected_value"])

    def choosePass(self, current_card_type: Optional[CardTypeResult] = None) -> bool:
        """判断是否应当过牌；基础规则仅在没有合法候选时过牌。"""
        if current_card_type is None:
            current_card_type = self._current_card_type()
        return self.recommend(current_card_type) == []

    def play(self) -> Turn:
        """在当前 Game 回合中执行推荐动作，并返回原生 Turn 对象。"""
        round_obj = self.game.current_round
        if round_obj is None:
            raise ValueError("Game 尚未开始，无法执行 AI 出牌")
        if round_obj.players[round_obj.current_player_index] is not self.player:
            raise ValueError("当前尚未轮到该 AI 玩家")

        current_type = self._current_card_type()
        cards = self.recommend(current_type)
        if cards:
            turn = self.game.play_turn(self.player, cards)
            self.game.check_winner()
            return turn

        return self.game.pass_turn(self.player)


class Aggressive(RuleAIPlayer):
    """进攻型：优先跑牌，积极使用炸弹并争夺主动权。"""

    style = "aggressive"

    def _style_adjustment(self, cards, card_type, current_card_type) -> float:
        is_bomb = bool(card_type and card_type["type"] in BOMB_TYPES)
        opponent_endgame = any(player.team_id != self.player.team_id and len(player.hand) <= 5 for player in self.game.players)
        bomb_needed = bool(current_card_type and current_card_type["type"] in BOMB_TYPES)
        bomb_justified = bool(is_bomb and (bomb_needed or len(self.player.hand) <= 8 or opponent_endgame))
        return 0.3 if bomb_justified else (0.08 if cards and not is_bomb else 0.0)


class Balanced(RuleAIPlayer):
    """均衡型：追求单次收益，同时适度保留炸弹。"""

    style = "balanced"

    pass


class Conservative(RuleAIPlayer):
    """保守型：帮助队友、保留炸弹，并在残局加强控制。"""

    style = "conservative"

    def choosePass(self, current_card_type: Optional[CardTypeResult] = None) -> bool:
        """队友掌握牌权时主动配合过牌，否则按可压制性判断。"""
        if self._partner_has_control():
            return True
        return super().choosePass(current_card_type)

    def _style_adjustment(self, cards, card_type, current_card_type) -> float:
        is_bomb = bool(card_type and card_type["type"] in BOMB_TYPES)
        return 0.15 if not is_bomb else -0.12


__all__ = ["RuleAIPlayer", "Aggressive", "Balanced", "Conservative"]
