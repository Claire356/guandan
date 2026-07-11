class Rulebook:
    """掼蛋规则说明与规则常量。"""

    PLAYER_COUNT = 4
    TOTAL_CARD_COUNT = 108
    CARDS_PER_PLAYER = 27
    TEAM_COUNT = 2
    TEAM_SIZE = 2

    # 规则说明：本项目为单机训练引擎骨架，重点在于核心流转。
    RULE_SUMMARY = [
        "使用两副扑克牌，共 108 张。",
        "四名玩家分成两队，玩家与 AI 队友对战两名 AI。",
        "每位玩家初始手牌 27 张。",
        "支持单张、对子、三张、炸弹、顺子、连对等基础牌型。",
        "支持升级、逢人配、进贡、还贡等规则入口。",
    ]
