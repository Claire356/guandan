"""严格按 DB3208/T 235—2025 实现的掼蛋牌型识别与比较。"""

from collections import Counter
from itertools import product
from typing import Iterable, List, Tuple, TypedDict

from .card import Card

INVALID = "invalid"
SINGLE = "single"
PAIR = "pair"
TRIPLE = "triple"
TRIPLE_WITH_PAIR = "triple_with_pair"
STRAIGHT = "straight"
DOUBLE_SEQUENCE = "double_sequence"
STEEL_PLATE = "steel_plate"
BOMB = "bomb"
STRAIGHT_FLUSH = "straight_flush"
JOKER_BOMB = "joker_bomb"

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["♠", "♥", "♣", "♦"]
BASE_LEVEL = {rank: index + 2 for index, rank in enumerate(RANKS)}


class CardTypeResult(TypedDict):
    type: str
    level: int
    length: int


def _result(card_type: str, level: int, length: int) -> CardTypeResult:
    return {"type": card_type, "level": level, "length": length}


def card_strength(card: Card, current_level: str = "2") -> int:
    """单张/对子/三张点力：大王>小王>级牌>A…2。"""
    if card.is_joker:
        return 17 if card.color == "red" or card.value >= 17 else 16
    return 15 if card.rank == current_level else BASE_LEVEL[card.rank]


def is_wild_card(card: Card, current_level: str = "2") -> bool:
    """红桃级牌为逢人配；大小王永远不是配牌。"""
    return not card.is_joker and card.suit == "♥" and card.rank == current_level


STRAIGHT_WINDOWS = [
    ["A", "2", "3", "4", "5"],
    ["2", "3", "4", "5", "6"],
    ["3", "4", "5", "6", "7"],
    ["4", "5", "6", "7", "8"],
    ["5", "6", "7", "8", "9"],
    ["6", "7", "8", "9", "10"],
    ["7", "8", "9", "10", "J"],
    ["8", "9", "10", "J", "Q"],
    ["9", "10", "J", "Q", "K"],
    ["10", "J", "Q", "K", "A"],
]
PAIR_WINDOWS = [["A", "2", "3"]] + [RANKS[index:index + 3] for index in range(0, 11)]
STEEL_WINDOWS = [["A", "2"]] + [RANKS[index:index + 2] for index in range(0, 12)]


def _window_level(ranks: Iterable[str], windows: List[List[str]]) -> int:
    rank_list = list(ranks)
    for index, window in enumerate(windows):
        if Counter(rank_list) == Counter(window):
            # A 在低端窗口只作 1 使用；其余窗口以最高牌点作为比较值。
            if index == 0 and window[0] == "A":
                return BASE_LEVEL[window[-1]]
            return BASE_LEVEL[window[-1]]
    return 0


def _natural_types(cards: List[Card], current_level: str) -> List[CardTypeResult]:
    """识别一组已经完成配牌替换的实体牌，可返回歧义牌型集合。"""
    length = len(cards)
    if not length:
        return []
    ranks = [card.rank for card in cards]
    counts = Counter(ranks)
    count_values = sorted(counts.values(), reverse=True)
    results: List[CardTypeResult] = []

    if length == 4 and all(card.is_joker for card in cards):
        joker_counts = Counter(card.color for card in cards)
        if joker_counts["black"] == 2 and joker_counts["red"] == 2:
            return [_result(JOKER_BOMB, 17, 4)]

    if length == 1:
        return [_result(SINGLE, card_strength(cards[0], current_level), 1)]
    if len(counts) == 1 and length == 2:
        return [_result(PAIR, max(card_strength(card, current_level) for card in cards), 2)]
    if len(counts) == 1 and length == 3 and not cards[0].is_joker:
        return [_result(TRIPLE, card_strength(cards[0], current_level), 3)]
    if len(counts) == 1 and 4 <= length <= 10 and not cards[0].is_joker:
        results.append(_result(BOMB, card_strength(cards[0], current_level), length))

    if length == 5 and count_values == [3, 2]:
        triple_rank = next(rank for rank, count in counts.items() if count == 3)
        triple_card = next(card for card in cards if card.rank == triple_rank)
        if not triple_card.is_joker:
            results.append(_result(TRIPLE_WITH_PAIR, card_strength(triple_card, current_level), 5))

    if not any(card.is_joker for card in cards):
        if length == 5 and len(counts) == 5:
            level = _window_level(ranks, STRAIGHT_WINDOWS)
            if level:
                type_name = STRAIGHT_FLUSH if len({card.suit for card in cards}) == 1 else STRAIGHT
                results.append(_result(type_name, level, 5))
        if length == 6 and count_values == [2, 2, 2]:
            level = _window_level(counts.keys(), PAIR_WINDOWS)
            if level:
                results.append(_result(DOUBLE_SEQUENCE, level, 6))
        if length == 6 and count_values == [3, 3]:
            level = _window_level(counts.keys(), STEEL_WINDOWS)
            if level:
                results.append(_result(STEEL_PLATE, level, 6))
    return results


def _result_key(result: CardTypeResult) -> Tuple[str, int, int]:
    return result["type"], result["level"], result["length"]


def identify_all_card_types(cards: List[Card], current_level: str = "2") -> List[CardTypeResult]:
    """返回逢人配所有合法解释；无配牌时红桃级牌按普通级牌使用。"""
    if current_level not in RANKS:
        raise ValueError("current_level 必须是 2 至 A")
    if not cards:
        return [_result(INVALID, 0, 0)]
    wilds = [card for card in cards if is_wild_card(card, current_level)]
    if not wilds or len(wilds) == len(cards):
        natural = _natural_types(cards, current_level)
        return natural or [_result(INVALID, 0, len(cards))]

    fixed = list(cards)
    wild_indices = [index for index, card in enumerate(cards) if is_wild_card(card, current_level)]
    replacements = [Card(suit, rank, BASE_LEVEL[rank]) for suit in SUITS for rank in RANKS]
    found = {}
    for choices in product(replacements, repeat=len(wild_indices)):
        interpreted = list(fixed)
        for index, replacement in zip(wild_indices, choices):
            interpreted[index] = replacement
        for result in _natural_types(interpreted, current_level):
            # 替换池没有大小王，因此逢人配绝不可能组成四王炸。
            found[_result_key(result)] = result
    return list(found.values()) or [_result(INVALID, 0, len(cards))]


def _bomb_strength(card_type: CardTypeResult) -> Tuple[int, int, int]:
    type_name, length, level = card_type["type"], card_type["length"], card_type["level"]
    if type_name == JOKER_BOMB:
        return 100, length, level
    if type_name == BOMB:
        return (60 + length if length >= 6 else length * 10), length, level
    if type_name == STRAIGHT_FLUSH:
        return 55, length, level
    return 0, length, level


def _default_strength(result: CardTypeResult) -> Tuple[int, int, int]:
    """逢人配多解默认取大；钢板优先于同组可解释的三连对。"""
    if result["type"] in {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}:
        return _bomb_strength(result)
    priority = {STEEL_PLATE: 9, DOUBLE_SEQUENCE: 8, TRIPLE_WITH_PAIR: 7, TRIPLE: 6, PAIR: 5, STRAIGHT: 4, SINGLE: 3}
    return priority.get(result["type"], 0), result["level"], result["length"]


def identify_card_type(cards: List[Card], current_level: str = "2") -> CardTypeResult:
    """识别默认最大牌型，接口保持 ``{type, level, length}``。"""
    results = identify_all_card_types(cards, current_level)
    valid = [result for result in results if result["type"] != INVALID]
    return max(valid, key=_default_strength) if valid else results[0]


def get_card_type(cards: List[Card], current_level: str = "2") -> CardTypeResult:
    return identify_card_type(cards, current_level)


def compare(card_type1: CardTypeResult, card_type2: CardTypeResult) -> int:
    """比较牌型；炸弹层级严格为四王>六张以上>同花顺>五炸>四炸。"""
    required = {"type", "level", "length"}
    if not required.issubset(card_type1) or not required.issubset(card_type2):
        raise ValueError("牌型结果必须包含 type、level 和 length")
    if card_type1["type"] == INVALID or card_type2["type"] == INVALID:
        raise ValueError("无效牌型不能比较")
    bombs = {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}
    bomb1, bomb2 = card_type1["type"] in bombs, card_type2["type"] in bombs
    if bomb1 or bomb2:
        if bomb1 != bomb2:
            return 1 if bomb1 else -1
        left, right = _bomb_strength(card_type1), _bomb_strength(card_type2)
        return (left > right) - (left < right)
    if card_type1["type"] != card_type2["type"] or card_type1["length"] != card_type2["length"]:
        return 0
    return (card_type1["level"] > card_type2["level"]) - (card_type1["level"] < card_type2["level"])


__all__ = [
    "INVALID", "SINGLE", "PAIR", "TRIPLE", "TRIPLE_WITH_PAIR", "STRAIGHT",
    "DOUBLE_SEQUENCE", "STEEL_PLATE", "BOMB", "STRAIGHT_FLUSH", "JOKER_BOMB",
    "CardTypeResult", "card_strength", "is_wild_card", "identify_all_card_types",
    "identify_card_type", "get_card_type", "compare",
]
