"""掼蛋牌型识别与比较。"""

from collections import Counter
from typing import List, Tuple, TypedDict

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

class CardTypeResult(TypedDict):
    """牌型识别结果的固定字段。"""

    type: str
    level: int
    length: int


def _result(card_type: str, level: int, length: int) -> CardTypeResult:
    """生成统一的牌型结果。"""
    return {"type": card_type, "level": level, "length": length}


def _sequence_level(values: List[int]) -> int:
    """返回连续牌的最高点数；A2345 按五点顺子计算。"""
    unique_values = sorted(set(values))
    if unique_values == [3, 4, 5, 14, 15]:
        return 5
    if 15 in unique_values or any(value > 15 for value in unique_values):
        return 0
    if unique_values == list(range(unique_values[0], unique_values[0] + len(unique_values))):
        return unique_values[-1]
    return 0


def _is_joker_bomb(cards: List[Card]) -> bool:
    """两副牌的四张大小王组成王炸。"""
    if len(cards) != 4 or not all(card.is_joker for card in cards):
        return False
    joker_values = Counter(card.value for card in cards)
    return sorted(joker_values.values()) == [2, 2]


def identify_card_type(cards: List[Card]) -> CardTypeResult:
    """识别一组牌，返回类型、比较点数和牌张数。"""
    length = len(cards)
    if length == 0:
        return _result(INVALID, 0, 0)

    values = [card.value for card in cards]
    counts = Counter(values)
    count_values = sorted(counts.values(), reverse=True)

    # 王炸必须先于普通四张炸弹判断。
    if _is_joker_bomb(cards):
        return _result(JOKER_BOMB, max(values), length)

    # 单张、对子和三张均要求所有牌点数相同。
    if length == 1:
        return _result(SINGLE, values[0], length)
    if length == 2 and len(counts) == 1:
        return _result(PAIR, values[0], length)
    if length == 3 and len(counts) == 1:
        return _result(TRIPLE, values[0], length)

    # 四至十张同点数牌构成炸弹。
    if 4 <= length <= 10 and len(counts) == 1:
        return _result(BOMB, values[0], length)

    # 三带二由一个三张和一个对子组成，比较三张的点数。
    if length == 5 and count_values == [3, 2]:
        triple_level = next(value for value, count in counts.items() if count == 3)
        return _result(TRIPLE_WITH_PAIR, triple_level, length)

    # 顺子固定五张且点数各不相同；2 只能用于 A2345。
    if length == 5 and len(counts) == 5:
        level = _sequence_level(values)
        if level:
            # 五张同花连续牌优先识别为同花顺。
            if len({card.suit for card in cards}) == 1 and not any(card.is_joker for card in cards):
                return _result(STRAIGHT_FLUSH, level, length)
            return _result(STRAIGHT, level, length)

    # 连对固定六张，由三个点数连续的对子组成。
    if length == 6 and count_values == [2, 2, 2]:
        level = _sequence_level(list(counts.keys()))
        if level:
            return _result(DOUBLE_SEQUENCE, level, length)

    # 钢板固定六张，由两个点数连续的三张组成。
    if length == 6 and count_values == [3, 3]:
        levels = sorted(counts.keys())
        if levels[1] == levels[0] + 1 and levels[1] <= 14:
            return _result(STEEL_PLATE, levels[1], length)

    return _result(INVALID, 0, length)


def get_card_type(cards: List[Card]) -> CardTypeResult:
    """识别牌型的直观调用入口。"""
    return identify_card_type(cards)


def _bomb_strength(card_type: CardTypeResult) -> Tuple[int, int, int]:
    """按掼蛋炸弹层级生成可排序的比较值。"""
    type_name = card_type["type"]
    length = int(card_type["length"])
    level = int(card_type["level"])
    if type_name == JOKER_BOMB:
        return (100, length, level)
    if type_name == BOMB:
        # 六张以上炸弹高于同花顺；五张、四张炸弹依次更低。
        category = 60 + length if length >= 6 else length * 10
        return (category, length, level)
    if type_name == STRAIGHT_FLUSH:
        return (55, length, level)
    return (0, length, level)


def compare(card_type1: CardTypeResult, card_type2: CardTypeResult) -> int:
    """比较两个识别结果；前者大返回 1，相等返回 0，较小返回 -1。

    普通牌型必须类型和长度一致。不同的普通牌型无法互相压制，返回 0。
    炸弹、同花顺和王炸按炸弹层级比较，可以压制任何普通牌型。
    """
    required_keys = {"type", "level", "length"}
    if not required_keys.issubset(card_type1) or not required_keys.issubset(card_type2):
        raise ValueError("牌型结果必须包含 type、level 和 length")

    type1 = card_type1["type"]
    type2 = card_type2["type"]
    if type1 == INVALID or type2 == INVALID:
        raise ValueError("无效牌型不能比较")

    bomb_types = {BOMB, STRAIGHT_FLUSH, JOKER_BOMB}
    is_bomb1 = type1 in bomb_types
    is_bomb2 = type2 in bomb_types
    if is_bomb1 or is_bomb2:
        if is_bomb1 and not is_bomb2:
            return 1
        if not is_bomb1 and is_bomb2:
            return -1
        strength1 = _bomb_strength(card_type1)
        strength2 = _bomb_strength(card_type2)
        return (strength1 > strength2) - (strength1 < strength2)

    if type1 != type2 or card_type1["length"] != card_type2["length"]:
        return 0
    level1 = int(card_type1["level"])
    level2 = int(card_type2["level"])
    return (level1 > level2) - (level1 < level2)


__all__ = [
    "INVALID",
    "SINGLE",
    "PAIR",
    "TRIPLE",
    "TRIPLE_WITH_PAIR",
    "STRAIGHT",
    "DOUBLE_SEQUENCE",
    "STEEL_PLATE",
    "BOMB",
    "STRAIGHT_FLUSH",
    "JOKER_BOMB",
    "identify_card_type",
    "get_card_type",
    "compare",
]
