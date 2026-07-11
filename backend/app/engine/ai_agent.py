from typing import List

from .card import Card
from .player import Player


class AIAgent:
    """AI 出牌策略入口，当前为规则驱动的基础版本。"""

    def __init__(self, player: Player) -> None:
        self.player = player

    def choose_cards(self, available_cards: List[Card]) -> List[Card]:
        """从当前手牌中选择一组可出牌。"""
        if not available_cards:
            return []
        return [available_cards[0]]

    def choose_contribution(self) -> List[Card]:
        """选择进贡牌，当前优先选择最小牌。"""
        if not self.player.hand:
            return []
        return [self.player.hand[0]]

    def choose_return(self) -> List[Card]:
        """选择还贡牌，当前优先选择贡献牌中的第一张。"""
        if not self.player.contributions:
            return []
        return [self.player.contributions[0]]
