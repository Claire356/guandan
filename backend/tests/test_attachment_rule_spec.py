"""附件规则专项回归测试。"""

from backend.app.engine.card import Card
from backend.app.engine.card_type import BOMB, compare, recognize
from backend.app.engine.move_generator import get_all_legal_moves
from backend.app.engine.validator import validate_play


VALUES = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}


def card(rank, suit="♠"):
    return Card(suit, rank, VALUES[rank])


def test_heart_level_cannot_be_played_alone():
    assert recognize([card("2", "♥")], "2")["type"] == "invalid"


def test_non_heart_level_is_second_highest_ordinary_single():
    level = recognize([card("7", "♠")], "7")
    ace = recognize([card("A")], "7")
    assert compare(level, ace) > 0


def test_joker_pair_is_invalid():
    jokers = [Card("Joker", "Black Joker", 16, True, "black")] * 2
    assert recognize(jokers, "2")["type"] == "invalid"


def test_pair_same_rank_compares_highest_suit():
    spade_pair = recognize([card("8", "♠"), card("8", "♦")], "2")
    heart_pair = recognize([card("8", "♥"), card("8", "♣")], "2")
    assert compare(spade_pair, heart_pair) > 0


def test_straight_can_have_more_than_five_cards():
    result = recognize([card(rank) for rank in ("3", "4", "5", "6", "7", "8", "9")], "2")
    assert result == {"type": "straight", "level": 9, "length": 7}


def test_straight_cannot_contain_two():
    assert recognize([card(rank) for rank in ("A", "2", "3", "4", "5")], "7")["type"] == "invalid"


def test_long_double_sequence_and_steel_plate():
    pairs = [card(rank, suit) for rank in ("3", "4", "5", "6") for suit in ("♠", "♥")]
    triples = [card(rank, suit) for rank in ("8", "9", "10") for suit in ("♠", "♥", "♣")]
    assert recognize(pairs, "2")["type"] == "double_sequence"
    assert recognize(triples, "2")["type"] == "steel_plate"


def test_only_four_same_cards_make_bomb():
    assert recognize([card("8")] * 4, "2")["type"] == BOMB
    assert recognize([card("8")] * 5, "2")["type"] == "invalid"


def test_pure_bomb_beats_soft_bomb_of_same_rank():
    pure = recognize([card("8", suit) for suit in ("♠", "♥", "♣", "♦")], "2")
    soft = recognize([card("8", suit) for suit in ("♠", "♥", "♣")] + [card("2", "♥")], "2")
    assert compare(pure, soft) > 0


def test_higher_soft_bomb_still_beats_lower_pure_bomb():
    soft_nine = recognize([card("9", suit) for suit in ("♠", "♥", "♣")] + [card("2", "♥")], "2")
    pure_eight = recognize([card("8", suit) for suit in ("♠", "♥", "♣", "♦")], "2")
    assert compare(soft_nine, pure_eight) > 0


def test_four_bomb_beats_straight_flush():
    bomb = recognize([card("3")] * 4, "2")
    straight_flush = recognize([card(rank, "♠") for rank in ("10", "J", "Q", "K", "A")], "2")
    assert compare(bomb, straight_flush) > 0


def test_straight_flush_same_high_card_compares_suit():
    spades = recognize([card(rank, "♠") for rank in ("3", "4", "5", "6", "7")], "2")
    hearts = recognize([card(rank, "♥") for rank in ("3", "4", "5", "6", "7")], "2")
    assert compare(spades, hearts) > 0


def test_validator_rejects_wild_single():
    wild = card("2", "♥")
    assert not validate_play([wild], None, [wild], "2")["valid"]


def test_move_generator_never_returns_wild_single():
    wild, three = card("2", "♥"), card("3")
    moves = get_all_legal_moves([wild, three], None, "2")
    assert [wild] not in moves
    assert [three] in moves
