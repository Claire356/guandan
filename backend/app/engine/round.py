from typing import List, Optional

from .card import Card
from .patterns import PatternRegistry
from .player import Player
from .turn import Turn


class Round:
    """一局牌局中的回合管理，负责验证出牌规则。"""

    def __init__(self, players: List[Player]) -> None:
        self.players = players
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
        """识别牌型，支持单张、对子、三张、炸弹、顺子和连对。"""
        if not cards:
            return None
        if len(cards) == 1:
            return PatternRegistry.SINGLE
        if len(cards) == 2 and cards[0].value == cards[1].value:
            return PatternRegistry.PAIR
        if len(cards) == 3 and cards[0].value == cards[1].value == cards[2].value:
            return PatternRegistry.TRIPLE
        if len(cards) == 4 and cards[0].value == cards[1].value == cards[2].value == cards[3].value:
            return PatternRegistry.BOMB
        if len(cards) >= 5 and not any(card.is_joker for card in cards):
            sorted_cards = sorted(cards, key=lambda card: card.value)
            values = [card.value for card in sorted_cards]
            if values == list(range(values[0], values[0] + len(values))):
                return PatternRegistry.SEQUENCE
        if len(cards) >= 6 and len(cards) % 2 == 0 and not any(card.is_joker for card in cards):
            sorted_cards = sorted(cards, key=lambda card: card.value)
            pairs = [sorted_cards[i].value for i in range(0, len(sorted_cards), 2)]
            if all(sorted_cards[i].value == sorted_cards[i + 1].value for i in range(0, len(sorted_cards), 2)) and pairs == list(range(pairs[0], pairs[0] + len(pairs))):
                return PatternRegistry.DOUBLE_SEQUENCE
        return None

    def _is_valid_against_previous(self, pattern: str, previous_cards: List[Card], current_cards: List[Card]) -> bool:
        """判断当前牌是否满足压制上家规则。"""
        previous_pattern = self._detect_pattern(previous_cards)
        if previous_pattern is None or pattern is None:
            return False
        if previous_pattern == PatternRegistry.BOMB and pattern != PatternRegistry.BOMB:
            return False
        if previous_pattern != pattern and pattern != PatternRegistry.BOMB:
            return False
        if pattern == PatternRegistry.BOMB and previous_pattern != PatternRegistry.BOMB:
            return True
        if pattern == PatternRegistry.BOMB and previous_pattern == PatternRegistry.BOMB:
            return max(card.value for card in current_cards) > max(card.value for card in previous_cards)
        return max(card.value for card in current_cards) > max(card.value for card in previous_cards)
