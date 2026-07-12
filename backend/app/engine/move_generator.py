"""统一合法动作生成器；AI与其他调用方不得自行拼牌。"""

import logging
from collections import Counter
from typing import Dict, List, Optional, Tuple, Union

from .card import Card
from .card_type import (
    PAIR_WINDOWS,
    RANKS,
    STEEL_WINDOWS,
    STRAIGHT_WINDOWS,
    CardTypeResult,
    INVALID,
    compare,
    identify_all_card_types,
    is_wild_card,
    recognize,
)


logger = logging.getLogger(__name__)


def _candidate_moves(hand: List[Card], current_level: str) -> List[List[Card]]:
    """使用实体手牌和红桃级牌生成结构不同的合法牌型候选。"""
    candidates: Dict[Tuple[Card, ...], List[Card]] = {}
    wilds = [card for card in hand if is_wild_card(card, current_level)]
    normal = list(hand)
    for wild in wilds:
        normal.remove(wild)

    def add(cards: List[Card]) -> None:
        if cards and recognize(cards, current_level)["type"] != INVALID:
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
    for window, count in ((window, 1) for window in STRAIGHT_WINDOWS):
        cards = compose({rank: count for rank in window})
        if len(cards) == 5:
            add(cards)
    for window, count in [*((window, 2) for window in PAIR_WINDOWS), *((window, 3) for window in STEEL_WINDOWS)]:
        cards = compose({rank: count for rank in window})
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
    """生成候选后逐一执行recognize→validate_play→compare，只返回能合法压牌的动作。"""
    from .validator import is_card_type_result, validate_play

    if current_table is None or current_table == []:
        table_type: Optional[CardTypeResult] = None
    elif isinstance(current_table, dict):
        if not is_card_type_result(current_table):
            raise ValueError("当前桌面牌型无效")
        table_type = current_table
    elif isinstance(current_table, list) and all(isinstance(card, Card) for card in current_table):
        table_type = recognize(current_table, current_level)
        if table_type["type"] == INVALID:
            raise ValueError("当前桌面牌不构成合法牌型")
    else:
        raise ValueError("current_table 必须是桌面牌列表、牌型结果或None")

    legal_moves: List[List[Card]] = []
    for candidate in _candidate_moves(hand, current_level):
        result = validate_play(hand, table_type, candidate, current_level)
        comparison = "LEAD" if table_type is None else max(
            compare(item, table_type)
            for item in identify_all_card_types(candidate, current_level)
            if item["type"] != INVALID
        )
        logger.debug(
            "桌面=%s AI候选=%s compare=%s 结论=%s",
            table_type, [str(card) for card in candidate], comparison,
            "LEGAL" if result["valid"] else "PASS",
        )
        if result["valid"]:
            legal_moves.append(candidate)
    return legal_moves


__all__ = ["get_all_legal_moves"]
