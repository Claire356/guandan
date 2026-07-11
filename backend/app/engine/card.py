from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Card:
    """扑克牌对象，表示一张牌。"""

    suit: str
    rank: str
    value: int
    is_joker: bool = False
    color: Optional[str] = None

    def to_dict(self) -> dict:
        """将牌对象转为可序列化字典。"""
        return {
            "suit": self.suit,
            "rank": self.rank,
            "value": self.value,
            "is_joker": self.is_joker,
            "color": self.color,
        }

    def __str__(self) -> str:
        if self.is_joker:
            return self.rank
        return f"{self.suit}{self.rank}"
