"""人格评分独立配置；修改权重无需改动评分引擎。"""

from typing import Dict, List, Tuple


DIMENSIONS = ("attack", "cooperation", "risk", "hesitation", "emotion")

# 五个维度的初始中性分，所有累计结果最终都会限制在 0～100。
BASE_SCORES: Dict[str, float] = {
    "attack": 50.0,
    "cooperation": 50.0,
    "risk": 50.0,
    "hesitation": 50.0,
    "emotion": 50.0,
}

# 每个事件的维度增减完全独立配置；未列出的维度保持不变。
EVENT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "pass": {"attack": -1.0, "hesitation": 2.0, "risk": -1.0},
    "bomb_used": {"attack": 4.0, "risk": 5.0},
    "critical_bomb": {"attack": 8.0, "risk": 6.0, "emotion": 1.0},
    "bomb_retained": {"attack": -1.0, "risk": -2.0, "emotion": 1.0},
    "helped_partner": {"cooperation": 10.0, "emotion": 1.0},
    "split_cards": {"attack": 2.0, "risk": 4.0, "emotion": -1.0},
    "recommendation_click": {"hesitation": 1.0},
    "slow_thinking": {"hesitation": 5.0, "emotion": -1.0},
    "very_slow_thinking": {"hesitation": 3.0, "emotion": -4.0},
    "fast_critical_decision": {"attack": 2.0, "hesitation": -2.0, "emotion": 3.0},
    "normal_decision": {"emotion": 0.2},
}

# 时间阈值也独立配置，单位为毫秒。
THINKING_THRESHOLDS: Dict[str, float] = {
    "slow": 15_000.0,
    "very_slow": 30_000.0,
    "fast_critical": 3_000.0,
}

# 人格映射按顺序匹配。每个条件为：维度、比较符、阈值。
# 均衡稳健型作为最终兜底，因此没有条件。
PERSONALITY_RULES: List[Tuple[str, List[Tuple[str, str, float]]]] = [
    ("纠结犹豫型", [("hesitation", ">=", 70.0)]),
    ("情绪化型", [("emotion", "<=", 35.0)]),
    ("团队协作型", [("cooperation", ">=", 70.0)]),
    ("激进冲锋型", [("attack", ">=", 68.0), ("risk", ">=", 58.0)]),
    ("保守隐忍型", [("attack", "<=", 38.0), ("risk", "<=", 42.0)]),
    ("城府伪装型", [("emotion", ">=", 65.0), ("risk", ">=", 58.0), ("attack", "<=", 60.0)]),
    ("均衡稳健型", []),
]


__all__ = [
    "DIMENSIONS",
    "BASE_SCORES",
    "EVENT_WEIGHTS",
    "THINKING_THRESHOLDS",
    "PERSONALITY_RULES",
]
