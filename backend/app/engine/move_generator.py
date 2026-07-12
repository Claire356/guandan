"""统一合法动作生成器；AI与其他调用方不得自行拼牌。"""

import logging
from collections import Counter
from itertools import product
from typing import Dict, List, Optional, Tuple, Union

from .card import Card
from .card_type import (
    PAIR_WINDOWS,
    RANKS,
    STEEL_WINDOWS,
    STRAIGHT_WINDOWS,
    CardTypeResult,
    INVALID,
    BOMB,
    JOKER_BOMB,
    STRAIGHT_FLUSH,
    compare,
    identify_all_card_types,
    is_wild_card,
    recognize,
)


logger = logging.getLogger(__name__)


def _candidate_moves(
    hand: List[Card],
    current_level: str,
    allowed_types: Optional[set] = None,
) -> List[List[Card]]:
    """按附件规则生成普通牌、变长顺子/连对/钢板及逢人配候选。"""
    candidates: Dict[Tuple[Card, ...], List[Card]] = {}
    wilds = [card for card in hand if is_wild_card(card, current_level)]
    normal = list(hand)
    for wild in wilds:
        normal.remove(wild)

    def add(cards: List[Card]) -> None:
        # 候选统一在 get_all_legal_moves 中经过 validate_play，避免在此重复识别。
        if cards:
            candidates.setdefault(tuple(cards), list(cards))

    def compose_all(requirements: Dict[str, int], suit: Optional[str] = None) -> List[List[Card]]:
        """枚举满足各点数需求的实体牌选择，并用逢人配补足缺口。"""
        choices_per_rank = []
        for rank, count in requirements.items():
            available = [card for card in normal if card.rank == rank and (suit is None or card.suit == suit)]
            # 两副牌会产生大量规则等价的实体组合；每种“使用几张实体牌”的分配只保留
            # 花色最高的稳定代表，避免 AI 在同一逻辑动作上重复评分。
            suit_order = {"♠": 4, "♥": 3, "♣": 2, "♦": 1, "Joker": 0}
            available.sort(key=lambda card: suit_order.get(card.suit, 0), reverse=True)
            rank_choices = []
            for take in range(max(0, count - len(wilds)), min(count, len(available)) + 1):
                rank_choices.append((available[:take], count - take))
            choices_per_rank.append(rank_choices)
        results = []
        for selection in product(*choices_per_rank):
            missing = sum(item[1] for item in selection)
            if missing <= len(wilds):
                results.append([card for item in selection for card in item[0]] + wilds[:missing])
        return results

    def allowed(type_name: str) -> bool:
        return allowed_types is None or type_name in allowed_types

    for card in hand:
        # 附件规定红桃级牌不能单独打出。
        if allowed("single") and not is_wild_card(card, current_level):
            add([card])
    for rank in RANKS:
        # 同点数组合只需要对子、三同张和四张炸弹。
        count_types = ((2, "pair"), (3, "triple"), (4, BOMB))
        for count, type_name in count_types:
            if not allowed(type_name):
                continue
            for cards in compose_all({rank: count}):
                if len(cards) == count:
                    add(cards)
    for triple_rank in RANKS if allowed("triple_with_pair") else []:
        for pair_rank in RANKS:
            if triple_rank != pair_rank:
                for cards in compose_all({triple_rank: 3, pair_rank: 2}):
                    if len(cards) == 5:
                        add(cards)

    sequence_ranks = [rank for rank in RANKS if rank != "2"]
    # 顺子至少五张，连对至少三组，钢板至少两组，均可延伸到 A。
    for size, count in ((size, 1) for size in range(5, len(sequence_ranks) + 1)) if allowed("straight") else []:
        for start in range(0, len(sequence_ranks) - size + 1):
            for cards in compose_all({rank: count for rank in sequence_ranks[start:start + size]}):
                if len(cards) == size:
                    add(cards)
    for group_size, count in ((size, 2) for size in range(3, len(sequence_ranks) + 1)) if allowed("double_sequence") else []:
        for start in range(0, len(sequence_ranks) - group_size + 1):
            length = group_size * count
            for cards in compose_all({rank: count for rank in sequence_ranks[start:start + group_size]}):
                if len(cards) == length:
                    add(cards)
    for group_size, count in ((size, 3) for size in range(2, len(sequence_ranks) + 1)) if allowed("steel_plate") else []:
        for start in range(0, len(sequence_ranks) - group_size + 1):
            length = group_size * count
            for cards in compose_all({rank: count for rank in sequence_ranks[start:start + group_size]}):
                if len(cards) == length:
                    add(cards)
    for suit in ("♠", "♥", "♣", "♦") if allowed(STRAIGHT_FLUSH) else []:
        for window in STRAIGHT_WINDOWS:
            for cards in compose_all({rank: 1 for rank in window}, suit=suit):
                if len(cards) == 5:
                    add(cards)
    jokers = [card for card in normal if card.is_joker]
    if allowed(JOKER_BOMB) and Counter(card.color for card in jokers) == Counter({"black": 2, "red": 2}):
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

    if table_type is None:
        allowed_types = None
    elif table_type["type"] in {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}:
        allowed_types = {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}
    else:
        allowed_types = {table_type["type"], BOMB, STRAIGHT_FLUSH, JOKER_BOMB}

    legal_moves: List[List[Card]] = []
    for candidate in _candidate_moves(hand, current_level, allowed_types):
        result = validate_play(hand, table_type, candidate, current_level)
        comparison = "LEAD" if table_type is None else ("PASS" if not result["valid"] else compare(result["card_type"], table_type))
        logger.debug(
            "桌面=%s AI候选=%s compare=%s 结论=%s",
            table_type, [str(card) for card in candidate], comparison,
            "LEGAL" if result["valid"] else "PASS",
        )
        if result["valid"]:
            legal_moves.append(candidate)
    # 桌面已有牌时PASS始终是合法动作，用空列表作为稳定的兼容表示。
    if table_type is not None:
        legal_moves.append([])
    return legal_moves


__all__ = ["get_all_legal_moves"]
