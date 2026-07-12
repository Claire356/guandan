import unittest

from backend.app.engine.card import Card
from backend.app.engine.card_type import compare, get_card_type, identify_card_type


SUITS = ["♠", "♥", "♣", "♦"]
RANKS = {3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10", 11: "J", 12: "Q", 13: "K", 14: "A", 15: "2"}


def cards(values, suits=None):
    suits = suits or [SUITS[index % 4] for index in range(len(values))]
    return [Card(suit, RANKS[value], value) for value, suit in zip(values, suits)]


def jokers():
    return [
        Card("Joker", "Black Joker", 16, True, "black"),
        Card("Joker", "Black Joker", 16, True, "black"),
        Card("Joker", "Red Joker", 17, True, "red"),
        Card("Joker", "Red Joker", 17, True, "red"),
    ]


class CardTypeRecognitionTests(unittest.TestCase):
    def assert_type(self, value_list, expected_type, expected_level, suits=None):
        result = identify_card_type(cards(value_list, suits))
        self.assertEqual(result, {"type": expected_type, "level": expected_level, "length": len(value_list)})

    def test_01_empty_is_invalid(self): self.assertEqual(identify_card_type([]), {"type": "invalid", "level": 0, "length": 0})
    def test_02_single(self): self.assert_type([3], "single", 3)
    def test_03_single_red_joker(self): self.assertEqual(identify_card_type([jokers()[-1]])["type"], "single")
    def test_04_pair(self): self.assert_type([8, 8], "pair", 8)
    def test_05_non_pair(self): self.assert_type([8, 9], "invalid", 0)
    def test_06_triple(self): self.assert_type([12, 12, 12], "triple", 12)
    def test_07_non_triple(self): self.assert_type([12, 12, 13], "invalid", 0)
    def test_08_triple_with_pair(self): self.assert_type([9, 9, 9, 6, 6], "triple_with_pair", 9)
    def test_09_triple_with_pair_unsorted(self): self.assert_type([6, 9, 6, 9, 9], "triple_with_pair", 9)
    def test_10_full_house_wrong_groups(self): self.assert_type([9, 9, 9, 6, 7], "invalid", 0)
    def test_11_straight(self): self.assert_type([3, 4, 5, 6, 7], "straight", 7)
    def test_12_straight_unsorted(self): self.assert_type([8, 5, 7, 4, 6], "straight", 8)
    def test_13_high_straight(self): self.assert_type([10, 11, 12, 13, 14], "straight", 14)
    def test_14_low_ace_straight(self): self.assert_type([14, 15, 3, 4, 5], "straight", 5)
    def test_15_straight_cannot_end_with_two(self): self.assert_type([11, 12, 13, 14, 15], "invalid", 0)
    def test_16_straight_rejects_duplicate(self): self.assert_type([3, 4, 4, 5, 6], "invalid", 0)
    def test_17_double_sequence(self): self.assert_type([5, 5, 6, 6, 7, 7], "double_sequence", 7)
    def test_18_double_sequence_unsorted(self): self.assert_type([7, 5, 6, 7, 5, 6], "double_sequence", 7)
    def test_19_double_sequence_gap(self): self.assert_type([5, 5, 6, 6, 8, 8], "invalid", 0)
    def test_20_double_sequence_wrong_counts(self): self.assert_type([5, 5, 5, 6, 6, 7], "invalid", 0)
    def test_21_steel_plate(self): self.assert_type([9, 9, 9, 10, 10, 10], "steel_plate", 10)
    def test_22_steel_plate_unsorted(self): self.assert_type([10, 9, 10, 9, 10, 9], "steel_plate", 10)
    def test_23_steel_plate_gap(self): self.assert_type([9, 9, 9, 11, 11, 11], "invalid", 0)
    def test_24_four_card_bomb(self): self.assert_type([6] * 4, "bomb", 6)
    def test_25_five_card_bomb(self): self.assert_type([7] * 5, "bomb", 7)
    def test_26_six_card_bomb(self): self.assert_type([8] * 6, "bomb", 8)
    def test_27_seven_card_bomb(self): self.assert_type([9] * 7, "bomb", 9)
    def test_28_eight_card_bomb(self): self.assert_type([10] * 8, "bomb", 10)
    def test_29_nine_card_bomb(self): self.assert_type([11] * 9, "bomb", 11)
    def test_30_ten_card_bomb(self): self.assert_type([12] * 10, "bomb", 12)
    def test_31_eleven_cards_not_bomb(self): self.assert_type([13] * 11, "invalid", 0)
    def test_32_straight_flush(self): self.assert_type([4, 5, 6, 7, 8], "straight_flush", 8, ["♥"] * 5)
    def test_33_low_ace_straight_flush(self): self.assert_type([14, 15, 3, 4, 5], "straight_flush", 5, ["♠"] * 5)
    def test_34_mixed_suit_not_straight_flush(self): self.assert_type([4, 5, 6, 7, 8], "straight", 8)
    def test_35_joker_bomb(self): self.assertEqual(identify_card_type(jokers()), {"type": "joker_bomb", "level": 17, "length": 4})
    def test_36_four_same_jokers_are_invalid(self): self.assertEqual(identify_card_type([jokers()[0]] * 4)["type"], "invalid")
    def test_37_get_card_type_direct_call(self): self.assertEqual(get_card_type(cards([3]))["type"], "single")


class CardTypeComparisonTests(unittest.TestCase):
    def result(self, values, suits=None): return identify_card_type(cards(values, suits))
    def test_38_higher_single_wins(self): self.assertEqual(compare(self.result([10]), self.result([9])), 1)
    def test_39_lower_pair_loses(self): self.assertEqual(compare(self.result([6, 6]), self.result([7, 7])), -1)
    def test_40_equal_triples_tie(self): self.assertEqual(compare(self.result([8] * 3), self.result([8] * 3)), 0)
    def test_41_different_normal_types_do_not_compare(self): self.assertEqual(compare(self.result([8]), self.result([7, 7])), 0)
    def test_42_bomb_beats_normal_type(self): self.assertEqual(compare(self.result([3] * 4), self.result([14])), 1)
    def test_43_five_bomb_beats_four_bomb(self): self.assertEqual(compare(self.result([3] * 5), self.result([14] * 4)), 1)
    def test_44_straight_flush_beats_five_bomb(self): self.assertEqual(compare(self.result([3, 4, 5, 6, 7], ["♠"] * 5), self.result([14] * 5)), 1)
    def test_45_six_bomb_beats_straight_flush(self): self.assertEqual(compare(self.result([3] * 6), self.result([10, 11, 12, 13, 14], ["♥"] * 5)), 1)
    def test_46_longer_bomb_wins(self): self.assertEqual(compare(self.result([3] * 8), self.result([14] * 7)), 1)
    def test_47_same_length_bomb_compares_level(self): self.assertEqual(compare(self.result([9] * 6), self.result([8] * 6)), 1)
    def test_48_joker_bomb_is_highest(self): self.assertEqual(compare(identify_card_type(jokers()), self.result([14] * 10)), 1)
    def test_49_low_ace_straight_loses(self): self.assertEqual(compare(self.result([14, 15, 3, 4, 5]), self.result([3, 4, 5, 6, 7])), -1)
    def test_50_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            compare(identify_card_type([]), self.result([3]))
    def test_51_missing_key_raises(self):
        with self.assertRaises(ValueError):
            compare({"type": "single"}, self.result([3]))


if __name__ == "__main__":
    unittest.main()
