from typing import List

from .card import Card


class Player:
    """玩家对象，包含手牌、队伍和基础行为。"""

    def __init__(self, name: str, team_id: int = 0, is_human: bool = False) -> None:
        self.name = name
        self.team_id = team_id
        self.is_human = is_human
        self.hand: List[Card] = []
        self.contributions: List[Card] = []

    def receive_cards(self, cards: List[Card]) -> None:
        """收牌。"""
        self.hand.extend(cards)

    def play_cards(self, cards: List[Card]) -> None:
        """出牌，要求牌必须存在于手牌中。"""
        for card in cards:
            if card not in self.hand:
                raise ValueError(f"{self.name} 手中没有这张牌: {card}")

        new_hand = []
        for card in self.hand:
            if card in cards:
                remaining = cards.copy()
                try:
                    remaining.remove(card)
                except ValueError:
                    pass
                continue
            new_hand.append(card)
        self.hand = new_hand

    def has_cards(self, cards: List[Card]) -> bool:
        """判断是否拥有待出的牌。"""
        hand_copy = list(self.hand)
        for card in cards:
            if card not in hand_copy:
                return False
            hand_copy.remove(card)
        return True

    def give_contribution(self, cards: List[Card]) -> None:
        """进贡：把指定牌移入贡牌列表。"""
        if not self.has_cards(cards):
            raise ValueError(f"{self.name} 无法完成进贡")
        self.play_cards(cards)
        self.contributions.extend(cards)

    def return_contribution(self, cards: List[Card]) -> None:
        """还贡：把贡牌重新回到手牌。"""
        for card in cards:
            if card not in self.contributions:
                raise ValueError(f"{self.name} 没有这张贡牌: {card}")
        self.contributions = [card for card in self.contributions if card not in cards]
        self.receive_cards(cards)

    def upgrade(self) -> None:
        """升级规则占位：后续可扩展为具体的升级判断。"""
        pass

    def follow_partner(self, cards: List[Card]) -> None:
        """逢人配规则占位：后续可扩展为具体的配牌判断。"""
        if not self.has_cards(cards):
            raise ValueError(f"{self.name} 无法完成逢人配")
        self.play_cards(cards)

    def to_dict(self) -> dict:
        """序列化当前玩家状态。"""
        return {
            "name": self.name,
            "team_id": self.team_id,
            "is_human": self.is_human,
            "hand_count": len(self.hand),
            "contribution_count": len(self.contributions),
        }
