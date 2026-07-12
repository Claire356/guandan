"""可直接接入 Game 的规则型掼蛋 AI。"""

import logging
from typing import List, Optional, Tuple

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
from .validator import get_all_legal_moves, validate_play


BOMB_TYPES = {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}
logger = logging.getLogger(__name__)


class RuleAIPlayer:
    """三种规则策略共用的候选生成与出牌流程。"""

    style = "rule"

    def __init__(self, game: Game, player: Player) -> None:
        self.game = game
        self.player = player
        self.last_legal_moves: List[List[Card]] = []

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

    def _score(self, cards: List[Card], current_card_type: Optional[CardTypeResult]) -> Tuple[int, ...]:
        """子类实现策略评分，元组越大表示越优先。"""
        card_type = identify_card_type(cards, self.game.state.current_level)
        return (len(cards), int(card_type["level"]))

    def _partner_has_control(self) -> bool:
        """判断当前桌面最后出牌者是否为自己的对家队友。"""
        round_obj = self.game.current_round
        return bool(
            round_obj
            and round_obj.last_player
            and round_obj.last_player is not self.player
            and round_obj.last_player.team_id == self.player.team_id
        )

    def recommend(self, current_card_type: Optional[CardTypeResult] = None) -> List[Card]:
        """推荐一组牌；没有可压制的牌时返回空列表表示过牌。"""
        if current_card_type is None:
            current_card_type = self._current_card_type()
        candidates = self._legal_candidates(current_card_type)
        if not candidates:
            logger.debug("桌面=%s 最终推荐=PASS 原因=无合法动作", current_card_type)
            return []
        # 队友掌握牌权时不反压；唯一例外是当前一手可以直接出完，优先完成走牌。
        if current_card_type is not None and self._partner_has_control():
            finishing = [cards for cards in candidates if len(cards) == len(self.player.hand)]
            if not finishing:
                logger.debug("桌面=%s 最终推荐=PASS 原因=队友控权", current_card_type)
                return []
            candidates = finishing

        best = max(candidates, key=lambda cards: self._score(cards, current_card_type))
        # 逢人配能够组成张数更多的非炸弹时优先采用，避免把万能牌长期闲置。
        wild_candidates = [
            cards for cards in candidates
            if any(is_wild_card(card, self.game.state.current_level) for card in cards)
            and identify_card_type(cards, self.game.state.current_level)["type"] not in BOMB_TYPES
        ]
        if wild_candidates:
            best_wild = max(wild_candidates, key=lambda cards: self._score(cards, current_card_type))
            if len(best_wild) > len(best):
                best = best_wild

        # 最终推荐必须再次走 validate_play → compare；失败候选立即剔除并重新评分。
        while candidates:
            result = validate_play(self.player.hand, current_card_type, best, self.game.state.current_level)
            logger.debug(
                "桌面=%s AI候选=%s compare校验=%s 最终推荐=%s",
                current_card_type,
                [str(card) for card in best],
                result["reason"],
                [str(card) for card in best] if result["valid"] else "RETRY",
            )
            if result["valid"]:
                return best
            candidates.remove(best)
            if not candidates:
                break
            best = max(candidates, key=lambda cards: self._score(cards, current_card_type))
        logger.error("AI所有候选均未通过最终校验，强制PASS；桌面=%s", current_card_type)
        return []

    def recommend_with_reason(self) -> dict:
        """输出可解释推荐，同时兼顾队友、炸弹、牌权、残局、级牌与逢人配。"""
        current_type = self._current_card_type()
        cards = self.recommend(current_type)
        if not cards:
            partner_control = self._partner_has_control() if hasattr(self, "_partner_has_control") else False
            reason = "队友掌握牌权，选择PASS保留牌力" if partner_control else "没有能够合法压过当前牌型的组合，选择PASS"
            return {"recommend_cards": [], "reason": reason, "expected_value": 0.35}

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
        expected = min(0.95, 0.45 + len(cards) / max(1, len(self.player.hand)) + (0.12 if current_type else 0.05))
        return {"recommend_cards": cards, "reason": "；".join(reasons), "expected_value": round(expected, 2)}

    def chooseBomb(self, current_card_type: Optional[CardTypeResult] = None) -> List[Card]:
        """选择当前能出的最合适炸弹；不存在时返回空列表。"""
        if current_card_type is None:
            current_card_type = self._current_card_type()
        bombs = [
            cards
            for cards in self._legal_candidates(current_card_type)
            if identify_card_type(cards, self.game.state.current_level)["type"] in BOMB_TYPES
        ]
        if not bombs:
            return []
        return max(bombs, key=lambda cards: self._score(cards, current_card_type))

    def choosePass(self, current_card_type: Optional[CardTypeResult] = None) -> bool:
        """判断是否应当过牌；基础规则仅在没有合法候选时过牌。"""
        if current_card_type is None:
            current_card_type = self._current_card_type()
        return not self._legal_candidates(current_card_type)

    def play(self) -> Turn:
        """在当前 Game 回合中执行推荐动作，并返回原生 Turn 对象。"""
        round_obj = self.game.current_round
        if round_obj is None:
            raise ValueError("Game 尚未开始，无法执行 AI 出牌")
        if round_obj.players[round_obj.current_player_index] is not self.player:
            raise ValueError("当前尚未轮到该 AI 玩家")

        current_type = self._current_card_type()
        cards = [] if self.choosePass(current_type) else self.recommend(current_type)
        if cards:
            turn = self.game.play_turn(self.player, cards)
            self.game.check_winner()
            return turn

        # Game.play_turn 没有过牌参数，因此通过其当前 Round 的兼容接口执行过牌。
        turn = round_obj.play_turn(self.player, [], is_pass=True)
        self.game.state.current_player_index = round_obj.current_player_index
        self.game.state.current_turn_count += 1
        self.game.state.add_log(f"{self.player.name} 选择PASS")
        # 连续三家过牌后，最后出牌者重新获得主动权，清空桌面进入新墩。
        if len(round_obj.turn_history) >= 3 and all(item.is_pass for item in round_obj.turn_history[-3:]):
            round_obj.last_played_cards = None
            round_obj.last_card_type = None
            round_obj.last_player = None
            round_obj.phase = "waiting"
            self.game.state.last_played_cards = None
            self.game.state.last_player_name = None
        return turn


class Aggressive(RuleAIPlayer):
    """进攻型：优先跑牌，积极使用炸弹并争夺主动权。"""

    style = "aggressive"

    def _score(self, cards: List[Card], current_card_type: Optional[CardTypeResult]) -> Tuple[int, ...]:
        card_type = identify_card_type(cards, self.game.state.current_level)
        is_bomb = int(card_type["type"] in BOMB_TYPES)
        opponent_endgame = any(player.team_id != self.player.team_id and len(player.hand) <= 5 for player in self.game.players)
        bomb_needed = bool(current_card_type and current_card_type["type"] in BOMB_TYPES)
        bomb_justified = bool(is_bomb and (bomb_needed or len(self.player.hand) <= 8 or opponent_endgame))
        # 进攻不等于盲目开炸：常规阶段普通合法牌优先，残局、对手报牌或炸弹对抗时才奖励炸弹。
        resource_priority = 2 if bomb_justified else (0 if is_bomb else 1)
        return (resource_priority, len(cards), int(card_type["level"]))


class Balanced(RuleAIPlayer):
    """均衡型：追求单次收益，同时适度保留炸弹。"""

    style = "balanced"

    def _score(self, cards: List[Card], current_card_type: Optional[CardTypeResult]) -> Tuple[int, ...]:
        card_type = identify_card_type(cards, self.game.state.current_level)
        is_bomb = int(card_type["type"] in BOMB_TYPES)
        # 非必要时保炸；相同条件下优先多跑牌，再选择较低点数减少资源消耗。
        bomb_needed = int(current_card_type is not None and current_card_type["type"] in BOMB_TYPES)
        preserve_score = 0 if is_bomb and not bomb_needed else 1
        return (preserve_score, len(cards), -int(card_type["level"]))


class Conservative(RuleAIPlayer):
    """保守型：帮助队友、保留炸弹，并在残局加强控制。"""

    style = "conservative"

    def choosePass(self, current_card_type: Optional[CardTypeResult] = None) -> bool:
        """队友掌握牌权时主动配合过牌，否则按可压制性判断。"""
        if self._partner_has_control():
            return True
        return super().choosePass(current_card_type)

    def _score(self, cards: List[Card], current_card_type: Optional[CardTypeResult]) -> Tuple[int, ...]:
        card_type = identify_card_type(cards, self.game.state.current_level)
        is_bomb = int(card_type["type"] in BOMB_TYPES)
        endgame = len(self.player.hand) <= 8
        # 常规阶段优先保炸和低成本跟牌；残局优先一次跑出更多牌并取得高牌权。
        if endgame:
            return (1 - is_bomb, len(cards), int(card_type["level"]))
        return (1 - is_bomb, len(cards), -int(card_type["level"]))


__all__ = ["RuleAIPlayer", "Aggressive", "Balanced", "Conservative"]
