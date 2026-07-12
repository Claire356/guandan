"""玩家五维画像权重配置。

所有基准分、事件增量和时间阈值集中在本文件，评分引擎不写死业务权重。
"""

from typing import Dict


DIMENSIONS = ("aggression", "cooperation", "emotion", "risk", "decision")
BASE_SCORE = 50.0
SCORE_MIN = 0.0
SCORE_MAX = 100.0
PERSONALITY_BOUNDARY = 50.0

# 每一种可观测行为对五个维度的影响。正值表示更接近该维度的高分人格。
EVENT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "bomb_used": {"aggression": 4.0, "risk": 5.0},
    "critical_bomb": {"aggression": 7.0, "risk": 4.0},
    "control_contested": {"aggression": 3.0},
    "active_attack": {"aggression": 2.0},
    "played_over_partner": {"aggression": 2.0, "cooperation": -4.0},
    "partner_pass": {"cooperation": 7.0},
    "protected_partner": {"cooperation": 6.0},
    "feed_succeeded": {"cooperation": 8.0},
    "split_bomb_for_partner": {"cooperation": 5.0, "risk": 3.0},
    "yielded_control": {"cooperation": 4.0},
    "speed_changed_after_loss": {"emotion": 5.0},
    "speed_changed_after_win": {"emotion": 3.0},
    "high_decision_variance": {"emotion": 5.0, "decision": -2.0},
    "critical_play_fluctuation": {"emotion": 6.0},
    "early_big_card": {"risk": 4.0},
    "late_small_card": {"risk": 5.0},
    "split_cards": {"risk": 4.0},
    "high_card_used": {"aggression": 1.0, "risk": 2.0},
    "risky_play": {"risk": 5.0},
    "decision_under_4s": {"decision": 3.0},
    "slow_decision": {"decision": -4.0},
    "fast_critical_decision": {"decision": 5.0},
    "rapid_streak": {"decision": 4.0},
}

TIME_THRESHOLDS_MS = {
    "decisive": 4_000.0,
    "slow": 15_000.0,
    "critical_fast": 4_000.0,
}

LABELS = {
    "aggression": {"high": "侵略型", "low": "保守型"},
    "cooperation": {"high": "合作型", "low": "独狼型"},
    "emotion": {"high": "情绪型", "low": "冷静型"},
    "risk": {"high": "赌狗型", "low": "稳健型"},
    "decision": {"high": "果断型", "low": "犹豫型"},
}

EXPLANATIONS = {
    "侵略型": "你喜欢主动掌控牌局，乐于争夺牌权。",
    "保守型": "你更加注重资源管理，倾向等待最佳时机。",
    "合作型": "你愿意为了队友牺牲自己的牌型。",
    "独狼型": "你更关注自己的出牌效率，合作意识较弱。",
    "情绪型": "你的打法容易受到上一局输赢影响。",
    "冷静型": "你的决策较稳定，不容易受到情绪影响。",
    "赌狗型": "你更愿意冒险，追求高收益打法。",
    "稳健型": "你更重视胜率和稳定收益。",
    "果断型": "你决策迅速，执行力较强。",
    "犹豫型": "你会花更多时间思考最佳方案。",
}

# 附件中的五维加权比例。评分器只按名称读取，不在算法中写死比例。
COMPONENT_WEIGHTS = {
    "aggression": {"bomb_frequency": 0.30, "override_partner": 0.25, "play_speed": 0.25, "power_struggle": 0.20},
    "cooperation": {"protect_partner": 0.30, "let_partner_play": 0.25, "feed_success": 0.25, "break_bomb_for_partner": 0.20},
    "emotion": {"loss_impact": 0.35, "win_impact": 0.35, "speed_variance": 0.30},
    "risk": {"bomb_frequency": 0.25, "risky_big_cards": 0.25, "risky_small_cards": 0.20, "big_card_frequency": 0.15, "break_combinations": 0.15},
    "decision": {"quick_decision_ratio": 1.0},
}

__all__ = [
    "DIMENSIONS", "BASE_SCORE", "SCORE_MIN", "SCORE_MAX", "PERSONALITY_BOUNDARY",
    "EVENT_WEIGHTS", "TIME_THRESHOLDS_MS", "LABELS", "EXPLANATIONS", "COMPONENT_WEIGHTS",
]
