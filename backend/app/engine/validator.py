"""掼蛋出牌合法性验证。"""

from collections import Counter
from typing import List, Optional, TypedDict

from .card import Card
from .card_type import (
    VALID_CARD_TYPES,
    CardTypeResult,
    INVALID,
    compare,
    identify_all_card_types,
    recognize,
)


class ValidationResult(TypedDict):
    """出牌验证结果的固定字段。"""

    valid: bool
    reason: str
    card_type: CardTypeResult


def _validation_result(
    valid: bool,
    reason: str,
    card_type: CardTypeResult,
) -> ValidationResult:
    """统一构造验证结果，避免各分支遗漏返回字段。"""
    return {"valid": valid, "reason": reason, "card_type": card_type}


def _contains_all_cards(hand: List[Card], cards_to_play: List[Card]) -> bool:
    """按完整牌面和数量检查待出牌是否都在玩家手中。

    掼蛋使用两副牌，同一花色和点数可能出现两次，因此不能只用集合判断。
    多重计数既允许玩家打出实际持有的重复牌，也能阻止重复使用同一张不存在的牌。
    """
    hand_counts = Counter(hand)
    play_counts = Counter(cards_to_play)
    return all(hand_counts[card] >= count for card, count in play_counts.items())


def is_card_type_result(card_type: object) -> bool:
    """检查桌面牌型是否具备比较所需的字段和字段类型。"""
    if not isinstance(card_type, dict):
        return False
    if set(("type", "level", "length")) - set(card_type):
        return False
    fields_valid = (
        isinstance(card_type["type"], str)
        and card_type["type"] in VALID_CARD_TYPES
        and isinstance(card_type["level"], int)
        and not isinstance(card_type["level"], bool)
        and isinstance(card_type["length"], int)
        and not isinstance(card_type["length"], bool)
    )
    if not fields_valid:
        return False
    try:
        compare(card_type, card_type)
    except ValueError:
        return False
    return True


def validate_play(
    hand: List[Card],
    current_card_type: Optional[CardTypeResult],
    cards_to_play: List[Card],
    current_level: str = "2",
) -> ValidationResult:
    """验证一次准备中的出牌，但不修改玩家手牌。

    验证顺序遵循实际出牌流程：先检查输入和手牌归属，再识别牌型，最后判断
    是否能够压过桌面牌型。桌面没有牌时传入 ``None``，任意合法牌型均可首出。
    """
    invalid_type: CardTypeResult = {"type": INVALID, "level": 0, "length": len(cards_to_play)}

    # 空出牌不构成任何牌型，直接返回明确原因。
    if not cards_to_play:
        return _validation_result(False, "出牌不能为空", invalid_type)

    # 验证器只接受 Card，避免错误对象进入牌型识别后产生难以理解的属性异常。
    if not all(isinstance(card, Card) for card in hand):
        return _validation_result(False, "玩家手牌包含无效对象", invalid_type)
    if not all(isinstance(card, Card) for card in cards_to_play):
        return _validation_result(False, "准备出的牌包含无效对象", invalid_type)

    proposed_type = recognize(cards_to_play, current_level)

    # 待出牌每一种完整牌面的数量都不能超过手牌中的实际数量。
    if not _contains_all_cards(hand, cards_to_play):
        return _validation_result(False, "准备出的牌不在手牌中或存在重复出牌", proposed_type)

    # 只有 card_type 模块支持的完整牌型才能出牌。
    if proposed_type["type"] == INVALID:
        return _validation_result(False, "牌型不合法，不符合掼蛋规则", proposed_type)

    # 桌面没有上一手牌时，当前玩家可以打出任意合法牌型。
    if current_card_type is None:
        return _validation_result(True, "出牌合法", proposed_type)

    # 损坏或不完整的桌面状态无法用于安全比较。
    if not is_card_type_result(current_card_type):
        return _validation_result(False, "当前桌面牌型无效", proposed_type)
    if current_card_type["type"] == INVALID:
        return _validation_result(False, "当前桌面牌型无效", proposed_type)

    # compare 大于零表示准备出的牌能严格压过桌面牌；相等也不能出。
    proposed_types = [item for item in identify_all_card_types(cards_to_play, current_level) if item["type"] != INVALID]
    if not any(compare(item, current_card_type) > 0 for item in proposed_types):
        if proposed_type["type"] != current_card_type["type"]:
            reason = "牌型不同，无法压过当前桌面牌型"
        else:
            reason = "准备出的牌未能压过当前桌面牌型"
        return _validation_result(False, reason, proposed_type)

    return _validation_result(True, "出牌合法并压过当前桌面牌型", proposed_type)


__all__ = ["ValidationResult", "validate_play", "is_card_type_result"]
