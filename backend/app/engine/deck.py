import random
from typing import List

from .card import Card
from .rulebook import Rulebook


class Deck:
    """牌堆对象，负责构造、洗牌和发牌。"""

    def __init__(self) -> None:
        self.cards: List[Card] = self._build_deck()

    def _build_deck(self) -> List[Card]:
        """构造两副 108 张牌，包含常规花色和大小王。"""
        suits = ["♠", "♥", "♣", "♦"]
        ranks = ["3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A", "2"]

        cards: List[Card] = []
        for _ in range(2):
            for suit in suits:
                for rank in ranks:
                    value = self._rank_to_value(rank)
                    cards.append(Card(suit=suit, rank=rank, value=value, is_joker=False))

            cards.append(Card(suit="Joker", rank="Black Joker", value=16, is_joker=True, color="black"))
            cards.append(Card(suit="Joker", rank="Red Joker", value=17, is_joker=True, color="red"))

        return cards

    @staticmethod
    def _rank_to_value(rank: str) -> int:
        """将牌面映射为数值，便于大小比较。"""
        mapping = {
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
            "10": 10,
            "J": 11,
            "Q": 12,
            "K": 13,
            "A": 14,
            "2": 15,
        }
        return mapping[rank]

    def shuffle(self) -> None:
        """洗牌，确保顺序发生变化。"""
        original = list(self.cards)
        while self.cards == original:
            random.shuffle(self.cards)

    def draw(self) -> Card:
        """从牌堆顶部抽一张。"""
        if not self.cards:
            raise ValueError("牌堆已空")
        return self.cards.pop(0)

    def deal_to_players(self, players, cards_per_player: int = Rulebook.CARDS_PER_PLAYER) -> None:
        """将全部 108 张牌平均发给四家；掼蛋没有底牌。"""
        if len(players) != Rulebook.PLAYER_COUNT:
            raise ValueError("掼蛋必须由四名玩家参与")
        if cards_per_player != Rulebook.CARDS_PER_PLAYER:
            raise ValueError("掼蛋开局每位玩家必须发 27 张牌")
        if len(self.cards) != Rulebook.TOTAL_CARD_COUNT:
            raise ValueError("发牌前牌堆必须包含完整的 108 张牌")
        for _ in range(cards_per_player):
            for player in players:
                player.receive_cards([self.draw()])
        if self.cards:
            raise RuntimeError("发牌后不应存在底牌")
