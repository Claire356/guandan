from dataclasses import dataclass, field
from typing import List, Optional

from .card import Card


@dataclass
class GameState:
    """对局状态快照，便于后续 UI 或日志展示。"""

    current_player_index: int = 0
    current_level: str = "2"
    last_played_cards: Optional[List[Card]] = None
    last_player_name: Optional[str] = None
    phase: str = "ready"
    log: List[str] = field(default_factory=list)
    current_turn_count: int = 0
    finish_order: List[str] = field(default_factory=list)
    consecutive_passes: int = 0
    power_holder_name: Optional[str] = None
    trick_number: int = 1
    power_transfer: Optional[dict] = None

    def add_log(self, message: str) -> None:
        """追加一条日志。"""
        self.log.append(message)

    def to_dict(self) -> dict:
        """转为字典，方便序列化。"""
        return {
            "current_player_index": self.current_player_index,
            "current_level": self.current_level,
            "last_played_cards": [card.to_dict() for card in (self.last_played_cards or [])],
            "last_player_name": self.last_player_name,
            "phase": self.phase,
            "log": self.log,
            "current_turn_count": self.current_turn_count,
            "finish_order": list(self.finish_order),
            "consecutive_passes": self.consecutive_passes,
            "power_holder_name": self.power_holder_name,
            "trick_number": self.trick_number,
            "power_transfer": self.power_transfer,
        }
