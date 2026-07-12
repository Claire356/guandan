"""连续 PASS 计数与牌权交接状态机。"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PassCounter:
    """追踪当前一轮的连续 PASS 与最后非 PASS 出牌者。"""

    consecutive_passes: int = 0
    last_play_player_index: Optional[int] = None
    round_active: bool = False

    def record_play(self, player_index: int) -> None:
        """任何有效出牌都会重置连续 PASS，并更新最后出牌者。"""
        self.consecutive_passes = 0
        self.last_play_player_index = player_index
        self.round_active = True

    def record_pass(self) -> bool:
        """记录 PASS；第三次连续 PASS 返回 True。"""
        if not self.round_active:
            return False
        self.consecutive_passes += 1
        if self.consecutive_passes >= 3:
            self.round_active = False
            return True
        return False

    def reset_round(self) -> None:
        """牌权交接或接风后清空本轮计数。"""
        self.consecutive_passes = 0
        self.last_play_player_index = None
        self.round_active = False


class PowerTransferStateMachine:
    """牌权从首出、跟牌、轮次结束到新首出的最小状态机。"""

    WAITING_FOR_PLAY = "waiting_for_play"
    WAITING_FOR_RESPONSE = "waiting_for_response"
    ROUND_END = "round_end"

    def __init__(self) -> None:
        self.state = self.WAITING_FOR_PLAY

    def on_play(self) -> str:
        self.state = self.WAITING_FOR_RESPONSE
        return self.state

    def on_pass(self, should_transfer: bool) -> str:
        self.state = self.ROUND_END if should_transfer else self.WAITING_FOR_RESPONSE
        return self.state

    def on_power_transfer(self) -> str:
        self.state = self.WAITING_FOR_PLAY
        return self.state


__all__ = ["PassCounter", "PowerTransferStateMachine"]
