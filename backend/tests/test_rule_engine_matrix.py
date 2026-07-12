import unittest

from backend.app.engine.card import Card
from backend.app.engine.card_type import BOMB, STRAIGHT, compare, recognize
from backend.app.engine.validator import validate_play


RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
VALUES = {rank: index + 2 for index, rank in enumerate(RANKS)}


def card(rank, suit="♠"):
    return Card(suit, rank, VALUES[rank])


class CurrentLevelComparisonMatrixTests(unittest.TestCase):
    """13个当前级别×13种普通牌，确保级牌始终高于所有普通牌。"""


def _make_level_test(current_level, rival_rank):
    def test(self):
        level_type = recognize([card(current_level)], current_level)
        rival_type = recognize([card(rival_rank)], current_level)
        expected = 0 if current_level == rival_rank else 1
        self.assertEqual(compare(level_type, rival_type), expected)
    return test


for _level in RANKS:
    for _rival in RANKS:
        setattr(
            CurrentLevelComparisonMatrixTests,
            f"test_level_{_level}_beats_{_rival}".replace("10", "ten"),
            _make_level_test(_level, _rival),
        )


class RuleEngineRegressionTests(unittest.TestCase):
    def test_single_cannot_beat_triple(self):
        self.assertEqual(compare(recognize([card("A")]), recognize([card("3")] * 3)), 0)

    def test_pair_cannot_beat_straight(self):
        pair = recognize([card("A", "♠"), card("A", "♥")])
        straight = recognize([card(rank, suit) for rank, suit in zip(("3", "4", "5", "6", "7"), ("♠", "♥", "♣", "♦", "♠"))])
        self.assertEqual(compare(pair, straight), 0)

    def test_bomb_beats_normal(self):
        self.assertEqual(compare(recognize([card("3")] * 4), recognize([card("A")])), 1)

    def test_heart_level_makes_bomb(self):
        cards = [card("2", "♥"), card("3", "♠"), card("3", "♥"), card("3", "♣")]
        self.assertEqual(recognize(cards, "2")["type"], BOMB)

    def test_heart_level_makes_highest_available_straight(self):
        cards = [card("2", "♥"), card("4", "♠"), card("5", "♥"), card("6", "♣"), card("7", "♦")]
        self.assertEqual(recognize(cards, "2"), {"type": STRAIGHT, "level": 8, "length": 5})

    def test_six_cards_can_form_long_straight(self):
        cards = [card("2", "♥"), card("4"), card("5"), card("6"), card("7"), card("8")]
        self.assertEqual(recognize(cards, "2")["type"], STRAIGHT)

    def test_validate_rejects_single_over_triple(self):
        hand = [card("A")]
        self.assertFalse(validate_play(hand, recognize([card("3")] * 3), hand)["valid"])

    def test_validate_rejects_pair_over_straight(self):
        hand = [card("A", "♠"), card("A", "♥")]
        table = recognize([card(rank, suit) for rank, suit in zip(("3", "4", "5", "6", "7"), ("♠", "♥", "♣", "♦", "♠"))])
        self.assertFalse(validate_play(hand, table, hand)["valid"])


if __name__ == "__main__":
    unittest.main()
