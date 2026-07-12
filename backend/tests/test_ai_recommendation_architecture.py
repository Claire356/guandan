import unittest

from backend.app.engine.ai_player import Balanced
from backend.app.engine.card import Card
from backend.app.engine.card_type import recognize
from backend.app.engine.game import Game
from backend.app.engine.move_generator import get_all_legal_moves
from backend.app.engine.validator import validate_play


VALUES = {"2": 15, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9}
SUITS = ["♠", "♥", "♣", "♦"]


def cards(*ranks):
    return [Card(SUITS[index % 4], rank, VALUES[rank]) for index, rank in enumerate(ranks)]


def configured_ai(hand, table):
    game = Game()
    game.start_new_game()
    round_obj = game.current_round
    player = game.players[1]
    player.hand = list(hand)
    round_obj.current_player_index = 1
    round_obj.last_player = game.players[0]
    round_obj.last_played_cards = list(table)
    round_obj.last_card_type = recognize(list(table), game.state.current_level)
    return Balanced(game, player), round_obj.last_card_type


class AIRecommendationArchitectureTests(unittest.TestCase):
    def test_1_pair_table_only_higher_pairs_and_pass_are_legal(self):
        # 题目中的345667只有一张7；使用3456677才能合法包含66和77。
        ai, table_type = configured_ai(cards("3", "4", "5", "6", "6", "7", "7"), cards("4", "4"))
        legal = get_all_legal_moves(ai.player.hand, table_type, "2")
        signatures = {tuple(sorted(card.rank for card in move)) for move in legal}
        self.assertEqual(signatures, {(), ("6", "6"), ("7", "7")})
        recommendation = ai.recommend(table_type)
        self.assertEqual(tuple(sorted(card.rank for card in recommendation)), ("6", "6"))
        self.assertNotIn(("4",), signatures)
        self.assertNotIn(("5",), signatures)
        self.assertNotIn(("3", "4", "5"), signatures)

    def test_2_triple_888_recommends_triple_999(self):
        ai, table_type = configured_ai(cards("9", "9", "9"), cards("8", "8", "8"))
        recommendation = ai.recommend(table_type)
        self.assertEqual([card.rank for card in recommendation], ["9", "9", "9"])

    def test_3_straight_table_never_recommends_pair(self):
        ai, table_type = configured_ai(cards("8", "8"), cards("3", "4", "5", "6", "7"))
        recommendation = ai.recommend(table_type)
        self.assertEqual(recommendation, [])

    def test_4_bomb_table_never_recommends_normal_cards(self):
        ai, table_type = configured_ai(cards("3", "4", "5", "9", "9", "9", "9"), cards("8", "8", "8", "8"))
        legal = get_all_legal_moves(ai.player.hand, table_type, "2")
        self.assertTrue(all(not move or recognize(move, "2")["type"] == "bomb" for move in legal))
        recommendation = ai.recommend(table_type)
        self.assertEqual(recognize(recommendation, "2")["type"], "bomb")

    def test_5_no_beating_move_recommends_pass(self):
        ai, table_type = configured_ai(cards("3"), cards("9"))
        recommendation = ai.recommend(table_type)
        self.assertEqual(recommendation, [])
        self.assertIn([], ai.last_legal_moves)

    def test_recommendation_is_member_of_legal_moves_and_has_scores(self):
        ai, table_type = configured_ai(cards("6", "6", "7", "7"), cards("4", "4"))
        recommendation = ai.recommend(table_type)
        self.assertIn(recommendation, ai.last_legal_moves)
        self.assertTrue(validate_play(ai.player.hand, table_type, recommendation, "2")["valid"])
        self.assertTrue(ai.last_evaluations)
        self.assertEqual(
            set(ai.last_evaluations[0]["score"]),
            {"expected_value", "bomb_retention_value", "cooperation_value", "endgame_value", "risk_value"},
        )


if __name__ == "__main__":
    unittest.main()
