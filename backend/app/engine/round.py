from typing import List, Optional

from .card import Card
from .card_type import INVALID, compare, identify_all_card_types, identify_card_type
from .player import Player
from .turn import Turn


class Round:
    """一局牌局中的回合管理，负责验证出牌规则。"""

    def __init__(self, players: List[Player], current_level: str = "2") -> None:
        self.players = players
        self.current_level = current_level
        self.current_player_index = 0
        self.turn_history: List[Turn] = []
        self.last_played_cards: Optional[List[Card]] = None
        self.last_player: Optional[Player] = None
        self.phase = "waiting"

    def play_turn(self, player: Player, cards: List[Card], is_pass: bool = False) -> Turn:
        """执行一次出牌动作。"""
        if player is not self.players[self.current_player_index]:
            return Turn(player, cards, "invalid", False, "当前不是该玩家出牌")

        if is_pass:
            self.phase = "pass"
            turn = Turn(player, cards, "pass", True, "选择弃牌", is_pass=True)
            self.turn_history.append(turn)
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            return turn

        if not cards:
            return Turn(player, cards, "invalid", False, "出牌不能为空")

        if not player.has_cards(cards):
            return Turn(player, cards, "invalid", False, "手牌中没有指定牌")

        pattern = self._detect_pattern(cards)
        if pattern is None:
            return Turn(player, cards, "invalid", False, "不支持的牌型")

        if self.last_played_cards is None:
            is_upgrade = False
            is_follow = False
        else:
            if not self._is_valid_against_previous(pattern, self.last_played_cards, cards):
                return Turn(player, cards, pattern, False, "牌型或牌值不满足压制条件")
            is_upgrade = True
            is_follow = False

        player.play_cards(cards)
        self.phase = "playing"
        turn = Turn(player, cards, pattern, True, "出牌成功", is_upgrade=is_upgrade, is_follow=is_follow)
        self.turn_history.append(turn)
        self.last_played_cards = list(cards)
        self.last_player = player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        return turn

    def _detect_pattern(self, cards: List[Card]) -> Optional[str]:
        """使用统一牌型模块识别，包含逢人配及全部竞赛牌型。"""
        result = identify_card_type(cards, self.current_level)
        return None if result["type"] == INVALID else result["type"]

    def _is_valid_against_previous(self, pattern: str, previous_cards: List[Card], current_cards: List[Card]) -> bool:
        """判断当前牌是否满足压制上家规则。"""
        if pattern is None:
            return False
        previous_types = [item for item in identify_all_card_types(previous_cards, self.current_level) if item["type"] != INVALID]
        current_types = [item for item in identify_all_card_types(current_cards, self.current_level) if item["type"] != INVALID]
        # 逢人配存在多种解释时，压牌方可选择任何能够合法压制的解释。
        return any(compare(current, previous) > 0 for current in current_types for previous in previous_types)
