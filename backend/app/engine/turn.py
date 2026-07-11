from dataclasses import dataclass
from typing import List, Optional

from .card import Card
from .player import Player


@dataclass
class Turn:
    """一次出牌动作。"""

    player: Player
    cards: List[Card]
    pattern: str
    is_valid: bool
    message: str = ""
    is_pass: bool = False
    is_upgrade: bool = False
    is_follow: bool = False

    def to_dict(self) -> dict:
        """将回合动作转为字典。"""
        return {
            "player": self.player.name,
            "cards": [card.to_dict() for card in self.cards],
            "pattern": self.pattern,
            "is_valid": self.is_valid,
            "message": self.message,
            "is_pass": self.is_pass,
            "is_upgrade": self.is_upgrade,
            "is_follow": self.is_follow,
        }
