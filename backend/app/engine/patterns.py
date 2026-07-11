from typing import List


class PatternRegistry:
    """牌型枚举与规则辅助。"""

    SINGLE = "single"
    PAIR = "pair"
    TRIPLE = "triple"
    BOMB = "bomb"
    SEQUENCE = "sequence"
    DOUBLE_SEQUENCE = "double_sequence"

    @classmethod
    def all_patterns(cls) -> List[str]:
        """返回当前支持的牌型。"""
        return [
            cls.SINGLE,
            cls.PAIR,
            cls.TRIPLE,
            cls.BOMB,
            cls.SEQUENCE,
            cls.DOUBLE_SEQUENCE,
        ]
