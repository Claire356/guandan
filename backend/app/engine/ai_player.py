"""可直接接入 Game 的规则型掼蛋 AI。"""

from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

from .card import Card
from .card_type import (
    BOMB,
    JOKER_BOMB,
    STRAIGHT_FLUSH,
    RANKS,
    STRAIGHT_WINDOWS,
    PAIR_WINDOWS,
    STEEL_WINDOWS,
    CardTypeResult,
    compare,
    identify_card_type,
    is_wild_card,
)
from .game import Game
from .player import Player
from .turn import Turn


BOMB_TYPES = {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}


class RuleAIPlayer:
    """三种规则策略共用的候选生成与出牌流程。"""

    style = "rule"

    def __init__(self, game: Game, player: Player) -> None:
        self.game = game
        self.player = player

    def _current_card_type(self) -> Optional[CardTypeResult]:
        """从当前 Game 中读取桌面牌型；新一轮主动出牌时返回 None。"""
        round_obj = self.game.current_round
        if round_obj is None or round_obj.last_played_cards is None:
            return None
        return identify_card_type(round_obj.last_played_cards, self.game.state.current_level)

    def _add_candidate(self, candidates: Dict[Tuple[Card, ...], List[Card]], cards: Sequence[Card]) -> None:
        """只保留能被现有牌型模块识别的候选，并去除重复候选。"""
        candidate = list(cards)
        if candidate and identify_card_type(candidate, self.game.state.current_level)["type"] != "invalid":
            candidates.setdefault(tuple(candidate), candidate)

    def _all_candidates(self) -> List[List[Card]]:
        """按牌点分组生成当前手牌能组成的全部核心牌型。

        这里不使用全组合穷举，避免在 27 张手牌上产生指数级开销。生成规则覆盖
        单张、对子、三张、三带二、顺子、连对、钢板、炸弹、同花顺和王炸。
        """
        candidates: Dict[Tuple[Card, ...], List[Card]] = {}
        level = self.game.state.current_level
        wilds = [card for card in self.player.hand if is_wild_card(card, level)]
        normal = [card for card in self.player.hand if card not in wilds]

        def compose(requirements: Dict[str, int], suit: Optional[str] = None) -> List[Card]:
            chosen: List[Card] = []
            missing = 0
            for rank, count in requirements.items():
                available = [card for card in normal if card.rank == rank and (suit is None or card.suit == suit)]
                chosen.extend(available[:count])
                missing += max(0, count - len(available))
            return chosen + wilds[:missing] if missing <= len(wilds) else []

        # 每张实体牌均可作为单张；逢人配单独出时按级牌使用。
        for card in self.player.hand:
            self._add_candidate(candidates, [card])

        # 对子、三张及4至10张炸弹均允许红桃级牌补足。
        for rank in RANKS:
            for count in range(2, 11):
                cards = compose({rank: count})
                if len(cards) == count:
                    self._add_candidate(candidates, cards)

        # 大小王只可自然组成对子；逢人配不能代替王。
        for color in ("black", "red"):
            jokers = [card for card in normal if card.is_joker and card.color == color]
            if len(jokers) >= 2:
                self._add_candidate(candidates, jokers[:2])

        # 三带二允许两张逢人配在三张与对子之间按合法需要分配。
        for triple_rank in RANKS:
            for pair_rank in RANKS:
                if triple_rank != pair_rank:
                    cards = compose({triple_rank: 3, pair_rank: 2})
                    if len(cards) == 5:
                        self._add_candidate(candidates, cards)

        for window in STRAIGHT_WINDOWS:
            cards = compose({rank: 1 for rank in window})
            if len(cards) == 5:
                self._add_candidate(candidates, cards)
        for window in PAIR_WINDOWS:
            cards = compose({rank: 2 for rank in window})
            if len(cards) == 6:
                self._add_candidate(candidates, cards)
        for window in STEEL_WINDOWS:
            cards = compose({rank: 3 for rank in window})
            if len(cards) == 6:
                self._add_candidate(candidates, cards)

        # 同花顺中逢人配可补成目标花色，但不能变成大小王。
        for suit in ("♠", "♥", "♣", "♦"):
            for window in STRAIGHT_WINDOWS:
                cards = compose({rank: 1 for rank in window}, suit=suit)
                if len(cards) == 5:
                    self._add_candidate(candidates, cards)

        # 两副牌中的两张小王和两张大王共同组成最高王炸。
        jokers = [card for card in normal if card.is_joker]
        joker_counts = Counter(card.value for card in jokers)
        if sorted(joker_counts.values()) == [2, 2]:
            self._add_candidate(candidates, jokers)
        return list(candidates.values())

    def _legal_candidates(self, current_card_type: Optional[CardTypeResult]) -> List[List[Card]]:
        """过滤出 Game 可执行且能严格压过当前桌面牌型的候选。

        完整牌型模块的覆盖范围大于现有 Round。为了不修改已经稳定的 Round，AI
        接入 Game 时只提交 Round 当前能执行的候选，避免推荐合法却无法落地的动作。
        """
        round_obj = self.game.current_round
        candidates = self._all_candidates()
        if round_obj is not None:
            candidates = [cards for cards in candidates if round_obj._detect_pattern(cards) is not None]
        if current_card_type is None:
            return candidates
        if round_obj is not None and round_obj.last_played_cards is not None:
            # 最终以接入对象自身的压制判断为准，保证 recommend 的结果可由 play 落地。
            return [
                cards
                for cards in candidates
                if round_obj._is_valid_against_previous(
                    round_obj._detect_pattern(cards),
                    round_obj.last_played_cards,
                    cards,
                )
            ]
        return [
            cards
            for cards in candidates
            if compare(identify_card_type(cards, self.game.state.current_level), current_card_type) > 0
        ]

    def _score(self, cards: List[Card], current_card_type: Optional[CardTypeResult]) -> Tuple[int, ...]:
        """子类实现策略评分，元组越大表示越优先。"""
        card_type = identify_card_type(cards, self.game.state.current_level)
        return (len(cards), int(card_type["level"]))

    def recommend(self, current_card_type: Optional[CardTypeResult] = None) -> List[Card]:
        """推荐一组牌；没有可压制的牌时返回空列表表示过牌。"""
        if current_card_type is None:
            current_card_type = self._current_card_type()
        candidates = self._legal_candidates(current_card_type)
        if not candidates:
            return []
        return max(candidates, key=lambda cards: self._score(cards, current_card_type))

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
        # 出牌张数优先，炸弹获得显著奖励，高点数用于积极争夺牌权。
        return (len(cards) + is_bomb * 5, is_bomb, int(card_type["level"]))


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

    def _partner_has_control(self) -> bool:
        """判断当前桌面最后出牌者是否为同队队友。"""
        round_obj = self.game.current_round
        return bool(
            round_obj
            and round_obj.last_player
            and round_obj.last_player is not self.player
            and round_obj.last_player.team_id == self.player.team_id
        )

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
        return (1 - is_bomb, -int(card_type["level"]), len(cards))


__all__ = ["RuleAIPlayer", "Aggressive", "Balanced", "Conservative"]
