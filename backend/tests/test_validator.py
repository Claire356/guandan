import unittest

from backend.app.engine.card import Card
from backend.app.engine.card_type import identify_card_type
from backend.app.engine.move_generator import get_all_legal_moves
from backend.app.engine.validator import validate_play


SUITS = ["♠", "♥", "♣", "♦"]
RANKS = {3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10", 11: "J", 12: "Q", 13: "K", 14: "A", 15: "2"}


def make_cards(values, suits=None):
    suits = suits or [SUITS[index % len(SUITS)] for index in range(len(values))]
    return [Card(suit, RANKS[value], value) for value, suit in zip(values, suits)]


def table(values, suits=None):
    return identify_card_type(make_cards(values, suits))


class ValidatorTests(unittest.TestCase):
    def validate(self, hand_values, play_values, current=None, hand_suits=None, play_suits=None):
        return validate_play(
            make_cards(hand_values, hand_suits),
            current,
            make_cards(play_values, play_suits),
        )

    def test_01_empty_play_is_invalid(self): self.assertFalse(validate_play([], None, [])["valid"])
    def test_02_single_lead_is_valid(self): self.assertTrue(self.validate([3], [3])["valid"])
    def test_03_pair_lead_is_valid(self): self.assertTrue(self.validate([6, 6], [6, 6])["valid"])
    def test_04_triple_lead_is_valid(self): self.assertTrue(self.validate([7, 7, 7], [7, 7, 7])["valid"])
    def test_05_full_house_lead_is_valid(self): self.assertTrue(self.validate([8, 8, 8, 5, 5], [8, 8, 8, 5, 5])["valid"])
    def test_06_straight_lead_is_valid(self): self.assertTrue(self.validate([3, 4, 5, 6, 7], [3, 4, 5, 6, 7])["valid"])
    def test_07_double_sequence_lead_is_valid(self): self.assertTrue(self.validate([3, 3, 4, 4, 5, 5], [3, 3, 4, 4, 5, 5])["valid"])
    def test_08_steel_plate_lead_is_valid(self): self.assertTrue(self.validate([6, 6, 6, 7, 7, 7], [6, 6, 6, 7, 7, 7])["valid"])
    def test_09_bomb_lead_is_valid(self): self.assertTrue(self.validate([9, 9, 9, 9], [9, 9, 9, 9])["valid"])
    def test_10_straight_flush_lead_is_valid(self): self.assertTrue(self.validate([3, 4, 5, 6, 7], [3, 4, 5, 6, 7], play_suits=["♥"] * 5, hand_suits=["♥"] * 5)["valid"])
    def test_11_card_missing_from_hand(self): self.assertFalse(self.validate([3], [4])["valid"])
    def test_12_duplicate_more_than_hand(self): self.assertFalse(self.validate([5], [5, 5])["valid"])
    def test_13_two_real_duplicates_are_allowed(self): self.assertTrue(self.validate([5, 5], [5, 5])["valid"])
    def test_14_three_requested_from_two_are_rejected(self): self.assertFalse(self.validate([5, 5], [5, 5, 5])["valid"])
    def test_15_same_rank_wrong_suit_is_missing(self): self.assertFalse(self.validate([7], [7], hand_suits=["♠"], play_suits=["♥"])["valid"])
    def test_16_invalid_pattern_is_rejected(self): self.assertFalse(self.validate([3, 3, 4], [3, 3, 4])["valid"])
    def test_17_higher_single_wins(self): self.assertTrue(self.validate([8], [8], table([7]))["valid"])
    def test_18_lower_single_loses(self): self.assertFalse(self.validate([7], [7], table([8]))["valid"])
    def test_19_equal_single_loses(self): self.assertFalse(self.validate([8], [8], table([8]))["valid"])
    def test_20_higher_pair_wins(self): self.assertTrue(self.validate([10, 10], [10, 10], table([9, 9]))["valid"])
    def test_21_different_normal_type_loses(self): self.assertFalse(self.validate([10, 10], [10, 10], table([9]))["valid"])
    def test_22_higher_straight_wins(self): self.assertTrue(self.validate([4, 5, 6, 7, 8], [4, 5, 6, 7, 8], table([3, 4, 5, 6, 7]))["valid"])
    def test_23_lower_straight_loses(self): self.assertFalse(self.validate([3, 4, 5, 6, 7], [3, 4, 5, 6, 7], table([4, 5, 6, 7, 8]))["valid"])
    def test_24_bomb_beats_single(self): self.assertTrue(self.validate([4, 4, 4, 4], [4, 4, 4, 4], table([14]))["valid"])
    def test_25_single_cannot_beat_bomb(self): self.assertFalse(self.validate([14], [14], table([4, 4, 4, 4]))["valid"])
    def test_26_five_same_is_not_a_bomb(self): self.assertFalse(self.validate([3] * 5, [3] * 5, table([14] * 4))["valid"])
    def test_27_lower_same_length_bomb_loses(self): self.assertFalse(self.validate([6] * 4, [6] * 4, table([7] * 4))["valid"])
    def test_28_invalid_current_type_is_rejected(self): self.assertFalse(self.validate([3], [3], {"type": "invalid", "level": 0, "length": 0})["valid"])
    def test_29_incomplete_current_type_is_rejected(self): self.assertFalse(self.validate([3], [3], {"type": "single"})["valid"])
    def test_30_result_has_exact_fields(self): self.assertEqual(set(self.validate([3], [3])), {"valid", "reason", "card_type"})
    def test_31_invalid_hand_object_is_rejected(self): self.assertFalse(validate_play([object()], None, make_cards([3]))["valid"])
    def test_32_invalid_play_object_is_rejected(self): self.assertFalse(validate_play(make_cards([3]), None, [object()])["valid"])
    def test_33_get_all_legal_moves_only_returns_cards_that_beat_table(self):
        hand = make_cards([3, 3, 3, 4, 4, 4, 4, 5, 5])
        current = table([3, 3, 3, 4, 4])
        moves = get_all_legal_moves(hand, current)
        self.assertTrue(moves)
        self.assertIn([], moves)
        self.assertTrue(all(validate_play(hand, current, move)["valid"] for move in moves if move))
        self.assertTrue(any(identify_card_type(move)["type"] == "triple_with_pair" and identify_card_type(move)["level"] == 4 for move in moves))
    def test_34_get_all_legal_moves_logs_compare_and_pass(self):
        with self.assertLogs("backend.app.engine.move_generator", level="DEBUG") as captured:
            get_all_legal_moves(make_cards([3, 4]), table([4]))
        output = " ".join(captured.output)
        self.assertIn("compare", output)
        self.assertIn("PASS", output)


if __name__ == "__main__":
    unittest.main()
