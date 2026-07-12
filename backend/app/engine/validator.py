"""掼蛋出牌合法性验证。"""

import logging
from collections import Counter
from typing import Dict, List, Optional, Tuple, TypedDict, Union

from .card import Card
from .card_type import (
    PAIR_WINDOWS,
    RANKS,
    STEEL_WINDOWS,
    STRAIGHT_WINDOWS,
    VALID_CARD_TYPES,
    CardTypeResult,
    INVALID,
    compare,
    identify_all_card_types,
    identify_card_type,
    is_wild_card,
)


logger = logging.getLogger(__name__)


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


def _is_card_type_result(card_type: object) -> bool:
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

    proposed_type = identify_card_type(cards_to_play, current_level)

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
    if not _is_card_type_result(current_card_type):
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


def _candidate_moves(hand: List[Card], current_level: str) -> List[List[Card]]:
    """从真实手牌生成所有结构不同的核心牌型候选，尚不判断能否压牌。"""
    candidates: Dict[Tuple[Card, ...], List[Card]] = {}
    wilds = [card for card in hand if is_wild_card(card, current_level)]
    normal = list(hand)
    for wild in wilds:
        normal.remove(wild)

    def add(cards: List[Card]) -> None:
        if cards and identify_card_type(cards, current_level)["type"] != INVALID:
            candidates.setdefault(tuple(cards), list(cards))

    def compose(requirements: Dict[str, int], suit: Optional[str] = None) -> List[Card]:
        chosen: List[Card] = []
        missing = 0
        for rank, count in requirements.items():
            available = [card for card in normal if card.rank == rank and (suit is None or card.suit == suit)]
            chosen.extend(available[:count])
            missing += max(0, count - len(available))
        return chosen + wilds[:missing] if missing <= len(wilds) else []

    for card in hand:
        add([card])
    for rank in RANKS:
        for count in range(2, 11):
            cards = compose({rank: count})
            if len(cards) == count:
                add(cards)
    for color in ("black", "red"):
        jokers = [card for card in normal if card.is_joker and card.color == color]
        if len(jokers) >= 2:
            add(jokers[:2])
    for triple_rank in RANKS:
        for pair_rank in RANKS:
            if triple_rank != pair_rank:
                cards = compose({triple_rank: 3, pair_rank: 2})
                if len(cards) == 5:
                    add(cards)
    for window in STRAIGHT_WINDOWS:
        cards = compose({rank: 1 for rank in window})
        if len(cards) == 5:
            add(cards)
    for window in PAIR_WINDOWS:
        cards = compose({rank: 2 for rank in window})
        if len(cards) == 6:
            add(cards)
    for window in STEEL_WINDOWS:
        cards = compose({rank: 3 for rank in window})
        if len(cards) == 6:
            add(cards)
    for suit in ("♠", "♥", "♣", "♦"):
        for window in STRAIGHT_WINDOWS:
            cards = compose({rank: 1 for rank in window}, suit=suit)
            if len(cards) == 5:
                add(cards)
    jokers = [card for card in normal if card.is_joker]
    if Counter(card.color for card in jokers) == Counter({"black": 2, "red": 2}):
        add(jokers)
    return list(candidates.values())


def get_all_legal_moves(
    hand: List[Card],
    current_table: Optional[Union[List[Card], CardTypeResult]],
    current_level: str = "2",
) -> List[List[Card]]:
    """返回当前手牌相对桌面的全部合法出牌；每个候选都必须通过validate_play和compare。"""
    if current_table is None or current_table == []:
        table_type: Optional[CardTypeResult] = None
    elif isinstance(current_table, dict):
        if not _is_card_type_result(current_table):
            raise ValueError("当前桌面牌型无效")
        table_type = current_table
    elif isinstance(current_table, list) and all(isinstance(card, Card) for card in current_table):
        table_type = identify_card_type(current_table, current_level)
        if table_type["type"] == INVALID:
            raise ValueError("当前桌面牌不构成合法牌型")
    else:
        raise ValueError("current_table 必须是桌面牌列表、牌型结果或None")

    legal_moves: List[List[Card]] = []
    for candidate in _candidate_moves(hand, current_level):
        result = validate_play(hand, table_type, candidate, current_level)
        candidate_type = result["card_type"]
        comparison = "LEAD" if table_type is None else max(
            compare(item, table_type)
            for item in identify_all_card_types(candidate, current_level)
            if item["type"] != INVALID
        )
        logger.debug(
            "桌面=%s AI候选=%s compare=%s 结论=%s",
            table_type,
            [str(card) for card in candidate],
            comparison,
            "LEGAL" if result["valid"] else "PASS",
        )
        if result["valid"]:
            legal_moves.append(candidate)
    return legal_moves


__all__ = ["ValidationResult", "validate_play", "get_all_legal_moves"]
