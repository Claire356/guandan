import unittest

from backend.app.engine import Card, Game, Player
from backend.app.engine.card_type import (
    BOMB,
    DOUBLE_SEQUENCE,
    JOKER_BOMB,
    STEEL_PLATE,
    STRAIGHT,
    STRAIGHT_FLUSH,
    card_strength,
    compare,
    identify_all_card_types,
    identify_card_type,
)


VALUES = {"2": 15, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}


def card(rank, suit="♠"):
    return Card(suit, rank, VALUES[rank])


def joker(color):
    return Card("Joker", "Red Joker" if color == "red" else "Black Joker", 17 if color == "red" else 16, True, color)


class HuaianCompetitionRuleTests(unittest.TestCase):
    def test_current_level_is_above_ace(self):
        self.assertGreater(card_strength(card("7"), "7"), card_strength(card("A"), "7"))

    def test_two_is_low_when_not_current_level(self):
        self.assertLess(card_strength(card("2"), "7"), card_strength(card("3"), "7"))

    def test_jokers_are_above_current_level(self):
        self.assertGreater(card_strength(joker("black"), "7"), card_strength(card("7"), "7"))
        self.assertGreater(card_strength(joker("red"), "7"), card_strength(joker("black"), "7"))

    def test_heart_level_completes_pair(self):
        result = identify_card_type([card("9"), card("7", "♥")], "7")
        self.assertEqual(result["type"], "pair")

    def test_heart_level_completes_bomb(self):
        cards = [card("9", suit) for suit in ("♠", "♥", "♣")] + [card("7", "♥")]
        self.assertEqual(identify_card_type(cards, "7")["type"], BOMB)

    def test_two_wilds_default_to_steel_plate(self):
        cards = [card("3", "♠"), card("3", "♣"), card("4", "♠"), card("4", "♣"), card("7", "♥"), card("7", "♥")]
        self.assertEqual(identify_card_type(cards, "7")["type"], STEEL_PLATE)
        self.assertIn(DOUBLE_SEQUENCE, {item["type"] for item in identify_all_card_types(cards, "7")})

    def test_wild_cannot_make_joker_bomb(self):
        cards = [joker("red"), joker("black"), card("7", "♥"), card("7", "♥")]
        self.assertNotEqual(identify_card_type(cards, "7")["type"], JOKER_BOMB)

    def test_four_jokers_make_joker_bomb(self):
        self.assertEqual(identify_card_type([joker("red"), joker("red"), joker("black"), joker("black")], "7")["type"], JOKER_BOMB)

    def test_a2345_is_not_a_straight(self):
        cards = [card(rank, suit) for rank, suit in zip(("A", "2", "3", "4", "5"), ("♠", "♥", "♣", "♦", "♠"))]
        self.assertEqual(identify_card_type(cards, "7")["type"], "invalid")

    def test_highest_straight(self):
        self.assertEqual(identify_card_type([card(rank) for rank in ("10", "J", "Q", "K", "A")], "7")["level"], 14)

    def test_three_pairs_cannot_contain_two(self):
        cards = [card(rank, suit) for rank in ("A", "2", "3") for suit in ("♠", "♥")]
        self.assertEqual(identify_card_type(cards, "7")["type"], "invalid")

    def test_highest_three_pairs(self):
        cards = [card(rank, suit) for rank in ("Q", "K", "A") for suit in ("♠", "♥")]
        self.assertEqual(identify_card_type(cards, "7")["level"], 14)

    def test_steel_plate_cannot_contain_two(self):
        cards = [card(rank, suit) for rank in ("A", "2") for suit in ("♠", "♥", "♣")]
        self.assertEqual(identify_card_type(cards, "7")["type"], "invalid")

    def test_four_bomb_beats_straight_flush(self):
        self.assertGreater(compare({"type": BOMB, "level": 3, "length": 4}, {"type": STRAIGHT_FLUSH, "level": 14, "length": 5}), 0)

    def test_straight_flush_beats_normal_type(self):
        self.assertGreater(compare({"type": STRAIGHT_FLUSH, "level": 5, "length": 5}, {"type": STRAIGHT, "level": 14, "length": 5}), 0)

    def test_five_same_is_not_bomb(self):
        self.assertEqual(identify_card_type([card("5")] * 5, "7")["type"], "invalid")

    def test_upgrade_by_partner_finish(self):
        self.assertEqual(Game.upgrade_steps(2), 3)
        self.assertEqual(Game.upgrade_steps(3), 2)
        self.assertEqual(Game.upgrade_steps(4), 1)

    def test_game_starts_at_level_two(self):
        game = Game()
        game.start_new_game()
        self.assertEqual(game.state.current_level, "2")
        self.assertEqual(game.to_dict()["currentLevel"], "2")

    def test_tribute_exchange_preserves_counts(self):
        game = Game()
        giver, receiver = Player("giver"), Player("receiver")
        game.players = [giver, receiver]
        tribute, returned = card("A"), card("10")
        giver.receive_cards([tribute, card("3")])
        receiver.receive_cards([returned, card("K")])
        game.exchange_tribute(giver, receiver, tribute, returned)
        self.assertEqual([len(giver.hand), len(receiver.hand)], [2, 2])
        self.assertIn(returned, giver.hand)
        self.assertIn(tribute, receiver.hand)

    def test_wild_level_card_cannot_be_tribute(self):
        game = Game()
        game.current_level = game.state.current_level = "7"
        giver, receiver = Player("giver"), Player("receiver")
        game.players = [giver, receiver]
        wild, ace, returned = card("7", "♥"), card("A"), card("3")
        giver.receive_cards([wild, ace])
        receiver.receive_cards([returned])
        with self.assertRaises(ValueError):
            game.exchange_tribute(giver, receiver, wild, returned)

    def test_two_red_jokers_must_belong_to_same_player(self):
        first, second = Player("first"), Player("second")
        first.receive_cards([joker("red")])
        second.receive_cards([joker("red")])
        self.assertFalse(Game.can_resist_tribute([first, second]))
        first.receive_cards([joker("red")])
        self.assertTrue(Game.can_resist_tribute([first, second]))


if __name__ == "__main__":
    unittest.main()
