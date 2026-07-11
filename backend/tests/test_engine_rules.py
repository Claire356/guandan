import unittest

from backend.app.engine import AIAgent, Game, Player, Rulebook


class EngineRulesTests(unittest.TestCase):
    def test_rulebook_constants(self):
        rulebook = Rulebook()
        self.assertEqual(rulebook.PLAYER_COUNT, 4)
        self.assertEqual(rulebook.CARDS_PER_PLAYER, 27)

    def test_ai_agent_can_choose_cards(self):
        player = Player("AI")
        ai = AIAgent(player)
        self.assertEqual(ai.choose_cards([]), [])

    def test_game_exposes_rulebook_context(self):
        game = Game(["你", "AI-1", "AI-2", "AI-3"])
        game.start_new_game()
        self.assertIsNotNone(game.current_round)
        self.assertEqual(game.current_round.phase, "waiting")

    def test_game_play_turn_updates_phase(self):
        game = Game(["你", "AI-1", "AI-2", "AI-3"])
        game.start_new_game()
        first_player = game.players[0]
        card = first_player.hand[0]
        turn = game.play_turn(first_player, [card])
        self.assertTrue(turn.is_valid)
        self.assertEqual(game.phase, "playing")

    def test_game_detects_team_winner(self):
        game = Game(["你", "AI-1", "AI-2", "AI-3"])
        game.start_new_game()
        for player in game.players:
            if player.team_id == 0:
                player.hand = []
        winner_team = game.check_winner_team()
        self.assertEqual(winner_team, 0)


if __name__ == "__main__":
    unittest.main()
