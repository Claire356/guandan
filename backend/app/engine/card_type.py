"""按项目附件规则实现的掼蛋牌型识别与大小比较。"""

from collections import Counter
from itertools import product
from typing import Iterable, List, Tuple

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
VALID_CARD_TYPES = {
    SINGLE, PAIR, TRIPLE, TRIPLE_WITH_PAIR, STRAIGHT, DOUBLE_SEQUENCE,
    STEEL_PLATE, BOMB, STRAIGHT_FLUSH, JOKER_BOMB,
}

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SEQUENCE_RANKS = ["3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["♠", "♥", "♣", "♦"]
BASE_LEVEL = {rank: index + 2 for index, rank in enumerate(RANKS)}
SUIT_LEVEL = {"♦": 1, "♣": 2, "♥": 3, "♠": 4}

# 保留旧模块导出的窗口常量，调用方接口不变；新规则允许更长的顺子、连对和钢板。
STRAIGHT_WINDOWS = [SEQUENCE_RANKS[index:index + 5] for index in range(len(SEQUENCE_RANKS) - 4)]
PAIR_WINDOWS = [SEQUENCE_RANKS[index:index + 3] for index in range(len(SEQUENCE_RANKS) - 2)]
STEEL_WINDOWS = [SEQUENCE_RANKS[index:index + 2] for index in range(len(SEQUENCE_RANKS) - 1)]


class CardTypeResult(dict):
    """保持公开字典仅含三字段，同时在对象属性中保存内部比较元数据。"""

    suit_level: int = 0
    pure: bool = False
    wildcard_count: int = 0


def _result(card_type: str, level: int, length: int, **extra: object) -> CardTypeResult:
    result = CardTypeResult(type=card_type, level=level, length=length)
    result.suit_level = int(extra.get("suit_level", 0))
    result.pure = bool(extra.get("pure", False))
    result.wildcard_count = int(extra.get("wildcard_count", 0))
    return result


def _meta(result: CardTypeResult, name: str, default: object = 0) -> object:
    """读取内部元数据，并兼容调用者手工构造的普通字典。"""
    return getattr(result, name, result.get(name, default))


def card_strength(card: Card, current_level: str = "2") -> int:
    """单牌牌力：大王>小王>级牌>A…2。"""
    if card.is_joker:
        return 17 if card.color == "red" or card.value >= 17 else 16
    return 15 if card.rank == current_level else BASE_LEVEL[card.rank]


def is_wild_card(card: Card, current_level: str = "2") -> bool:
    """只有红桃级牌是逢人配，且不能替代大小王。"""
    return not card.is_joker and card.suit == "♥" and card.rank == current_level


def _is_consecutive(ranks: Iterable[str]) -> bool:
    """检查不含 2 和王、仅在 3～A 区间内连续的点数。"""
    values = sorted(BASE_LEVEL[rank] for rank in ranks)
    return bool(values) and values == list(range(values[0], values[0] + len(values))) and values[0] >= 3


def _natural_types(cards: List[Card], current_level: str, wildcard_count: int = 0) -> List[CardTypeResult]:
    """识别一组已完成逢人配替换的牌，并保留比较需要的附加信息。"""
    length = len(cards)
    if not length:
        return []
    ranks = [card.rank for card in cards]
    counts = Counter(ranks)
    count_values = sorted(counts.values(), reverse=True)
    results: List[CardTypeResult] = []

    if length == 4 and all(card.is_joker for card in cards):
        colors = Counter(card.color for card in cards)
        if colors == Counter({"black": 2, "red": 2}):
            return [_result(JOKER_BOMB, 17, 4, pure=True, wildcard_count=0)]

    # 附件明确规定逢人配不能单独打出；该限制在展开前处理。
    if length == 1:
        return [_result(SINGLE, card_strength(cards[0], current_level), 1, suit_level=SUIT_LEVEL.get(cards[0].suit, 0))]

    # 对子不允许由大小王组成；同点数时以对子中最高花色比较。
    if length == 2 and len(counts) == 1 and not any(card.is_joker for card in cards):
        results.append(_result(
            PAIR,
            card_strength(cards[0], current_level),
            2,
            suit_level=max(SUIT_LEVEL.get(card.suit, 0) for card in cards),
            wildcard_count=wildcard_count,
        ))
    if length == 3 and len(counts) == 1 and not any(card.is_joker for card in cards):
        results.append(_result(TRIPLE, card_strength(cards[0], current_level), 3, wildcard_count=wildcard_count))
    if length == 5 and count_values == [3, 2] and not any(card.is_joker for card in cards):
        triple_rank = next(rank for rank, count in counts.items() if count == 3)
        results.append(_result(
            TRIPLE_WITH_PAIR,
            card_strength(next(card for card in cards if card.rank == triple_rank), current_level),
            5,
            wildcard_count=wildcard_count,
        ))

    # 新附件只把四张同点数定义为炸弹；同点数先比点数，再比纯炸与软炸。
    if length == 4 and len(counts) == 1 and not any(card.is_joker for card in cards):
        results.append(_result(
            BOMB,
            card_strength(cards[0], current_level),
            4,
            pure=wildcard_count == 0,
            wildcard_count=wildcard_count,
        ))

    if not any(card.is_joker for card in cards) and "2" not in counts:
        if length >= 5 and len(counts) == length and _is_consecutive(counts):
            level = max(BASE_LEVEL[rank] for rank in counts)
            # 同花顺严格为五张；普通顺子可以五张及以上。
            if length == 5 and len({card.suit for card in cards}) == 1:
                suit = cards[0].suit
                results.append(_result(
                    STRAIGHT_FLUSH, level, 5,
                    suit_level=SUIT_LEVEL[suit], wildcard_count=wildcard_count,
                ))
            results.append(_result(STRAIGHT, level, length, wildcard_count=wildcard_count))
        if length >= 6 and length % 2 == 0 and all(count == 2 for count in counts.values()) and len(counts) >= 3 and _is_consecutive(counts):
            results.append(_result(DOUBLE_SEQUENCE, max(BASE_LEVEL[rank] for rank in counts), length, wildcard_count=wildcard_count))
        if length >= 6 and length % 3 == 0 and all(count == 3 for count in counts.values()) and len(counts) >= 2 and _is_consecutive(counts):
            results.append(_result(STEEL_PLATE, max(BASE_LEVEL[rank] for rank in counts), length, wildcard_count=wildcard_count))
    return results


def _result_key(result: CardTypeResult) -> Tuple[object, ...]:
    return (
        result["type"], result["level"], result["length"], _meta(result, "suit_level", 0),
        _meta(result, "pure", False), _meta(result, "wildcard_count", 0),
    )


def identify_all_card_types(cards: List[Card], current_level: str = "2") -> List[CardTypeResult]:
    """枚举红桃级牌的所有合法替代，并返回全部合法牌型解释。"""
    if current_level not in RANKS:
        raise ValueError("current_level 必须是 2 至 A")
    if not cards:
        return [_result(INVALID, 0, 0)]
    wild_indices = [index for index, card in enumerate(cards) if is_wild_card(card, current_level)]
    if len(cards) == 1 and wild_indices:
        return [_result(INVALID, 0, 1)]
    if not wild_indices:
        natural = _natural_types(cards, current_level)
        return natural or [_result(INVALID, 0, len(cards))]

    # 替换池刻意不含王，确保逢人配不能组成天王炸。
    found = {}
    # 普通牌型只依赖替代点数；统一用黑桃可同时得到对子最高花色解释。
    # 同花顺另按四种花色补充检查，将搜索量从 52^n 降至 5×13^n。
    for rank_choices in product(RANKS, repeat=len(wild_indices)):
        interpreted = list(cards)
        for index, rank in zip(wild_indices, rank_choices):
            interpreted[index] = Card("♠", rank, BASE_LEVEL[rank])
        for result in _natural_types(interpreted, current_level, len(wild_indices)):
            found[_result_key(result)] = result
        for suit in SUITS:
            suited = list(cards)
            for index, rank in zip(wild_indices, rank_choices):
                suited[index] = Card(suit, rank, BASE_LEVEL[rank])
            for result in _natural_types(suited, current_level, len(wild_indices)):
                if result["type"] == STRAIGHT_FLUSH:
                    found[_result_key(result)] = result
    return list(found.values()) or [_result(INVALID, 0, len(cards))]


def _default_strength(result: CardTypeResult) -> Tuple[int, int, int, int, int]:
    """逢人配存在多解时，按附件牌型牌力选择最大合法解释。"""
    priority = {
        JOKER_BOMB: 100, BOMB: 90, STRAIGHT_FLUSH: 80,
        STEEL_PLATE: 60, DOUBLE_SEQUENCE: 55, TRIPLE_WITH_PAIR: 50,
        TRIPLE: 40, PAIR: 30, STRAIGHT: 20, SINGLE: 10,
    }
    return (
        priority.get(result["type"], 0), result["level"], result["length"],
        int(bool(_meta(result, "pure", False))), int(_meta(result, "suit_level", 0)),
    )


def recognize(cards: List[Card], current_level: str = "2") -> CardTypeResult:
    """展开全部逢人配解释并返回牌力最大的合法解释。"""
    results = identify_all_card_types(cards, current_level)
    valid = [result for result in results if result["type"] != INVALID]
    return max(valid, key=_default_strength) if valid else results[0]


def identify_card_type(cards: List[Card], current_level: str = "2") -> CardTypeResult:
    """兼容旧接口，统一委托给 recognize。"""
    return recognize(cards, current_level)


def get_card_type(cards: List[Card], current_level: str = "2") -> CardTypeResult:
    return recognize(cards, current_level)


def compare(card_type1: CardTypeResult, card_type2: CardTypeResult) -> int:
    """比较两手牌；不同普通牌型不可互压，炸弹遵循附件中的新层级。"""
    required = {"type", "level", "length"}
    if not required.issubset(card_type1) or not required.issubset(card_type2):
        raise ValueError("牌型结果必须包含 type、level 和 length")
    if card_type1["type"] == INVALID or card_type2["type"] == INVALID:
        raise ValueError("无效牌型不能比较")
    if card_type1["type"] not in VALID_CARD_TYPES or card_type2["type"] not in VALID_CARD_TYPES:
        raise ValueError("牌型名称不符合掼蛋规则")
    def valid_length(result: CardTypeResult) -> bool:
        type_name, length = result["type"], result["length"]
        if type_name == SINGLE: return length == 1
        if type_name == PAIR: return length == 2
        if type_name == TRIPLE: return length == 3
        if type_name == TRIPLE_WITH_PAIR: return length == 5
        if type_name == STRAIGHT: return length >= 5
        if type_name == DOUBLE_SEQUENCE: return length >= 6 and length % 2 == 0
        if type_name == STEEL_PLATE: return length >= 6 and length % 3 == 0
        if type_name == BOMB: return length == 4
        if type_name == STRAIGHT_FLUSH: return length == 5
        if type_name == JOKER_BOMB: return length == 4
        return False
    if not valid_length(card_type1) or not valid_length(card_type2):
        raise ValueError("牌型长度不符合掼蛋规则")

    bomb_types = {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}
    bomb1, bomb2 = card_type1["type"] in bomb_types, card_type2["type"] in bomb_types
    if bomb1 != bomb2:
        return 1 if bomb1 else -1
    if bomb1 and bomb2:
        category = {STRAIGHT_FLUSH: 1, BOMB: 2, JOKER_BOMB: 3}
        if category[card_type1["type"]] != category[card_type2["type"]]:
            return (category[card_type1["type"]] > category[card_type2["type"]]) - (category[card_type1["type"]] < category[card_type2["type"]])
        if card_type1["level"] != card_type2["level"]:
            return (card_type1["level"] > card_type2["level"]) - (card_type1["level"] < card_type2["level"])
        if card_type1["type"] == BOMB and bool(_meta(card_type1, "pure", False)) != bool(_meta(card_type2, "pure", False)):
            return 1 if bool(_meta(card_type1, "pure", False)) else -1
        if card_type1["type"] == STRAIGHT_FLUSH:
            left, right = int(_meta(card_type1, "suit_level", 0)), int(_meta(card_type2, "suit_level", 0))
            return (left > right) - (left < right)
        return 0

    if card_type1["type"] != card_type2["type"] or card_type1["length"] != card_type2["length"]:
        return 0
    if card_type1["level"] != card_type2["level"]:
        return (card_type1["level"] > card_type2["level"]) - (card_type1["level"] < card_type2["level"])
    if card_type1["type"] == PAIR:
        left, right = int(_meta(card_type1, "suit_level", 0)), int(_meta(card_type2, "suit_level", 0))
        return (left > right) - (left < right)
    return 0


__all__ = [
    "INVALID", "SINGLE", "PAIR", "TRIPLE", "TRIPLE_WITH_PAIR", "STRAIGHT",
    "DOUBLE_SEQUENCE", "STEEL_PLATE", "BOMB", "STRAIGHT_FLUSH", "JOKER_BOMB",
    "CardTypeResult", "card_strength", "is_wild_card", "identify_all_card_types",
    "recognize", "identify_card_type", "get_card_type", "compare", "VALID_CARD_TYPES",
    "RANKS", "BASE_LEVEL", "SUIT_LEVEL", "STRAIGHT_WINDOWS", "PAIR_WINDOWS", "STEEL_WINDOWS",
]
