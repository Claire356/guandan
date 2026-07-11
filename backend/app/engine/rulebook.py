class Rulebook:
    """掼蛋规则说明与规则常量。"""

    DECK_COUNT = 2
    CARDS_PER_DECK = 54
    PLAYER_COUNT = 4
    TOTAL_CARD_COUNT = 108
    CARDS_PER_PLAYER = 27
    BOTTOM_CARD_COUNT = 0
    HAS_BOTTOM_CARDS = False
    JOKER_COUNT = 4
    TEAM_COUNT = 2
    TEAM_SIZE = 2
    WILD_CARD_SUIT = "♥"
    TRIBUTE_PRESERVES_HAND_TOTAL = True

    @classmethod
    def is_wild_card(cls, card, level_rank: str) -> bool:
        """判断是否为本局逢人配：仅红桃花色的当前级牌可作配牌。"""
        return not card.is_joker and card.suit == cls.WILD_CARD_SUIT and card.rank == level_rank

    @staticmethod
    def exchange_preserves_total(before_counts, after_counts) -> bool:
        """校验进贡、还贡交换前后四家手牌总数没有变化。"""
        return sum(before_counts) == sum(after_counts)

    # 规则说明：本项目为单机训练引擎骨架，重点在于核心流转。
    RULE_SUMMARY = [
        "使用两副扑克牌，单副 54 张，共 108 张（含四张大小王）。",
        "四名玩家分成两队，玩家与 AI 队友对战两名 AI。",
        "无底牌，108 张牌平均发给四家，每位玩家开局 27 张。",
        "当前级牌中的红桃级牌为逢人配。",
        "进贡、还贡只在四家手牌之间交换，不增减手牌总数。",
        "支持单张、对子、三张、炸弹、顺子、连对等基础牌型。",
        "支持升级、逢人配、进贡、还贡等规则入口。",
    ]
