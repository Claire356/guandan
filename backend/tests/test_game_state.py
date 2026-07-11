import unittest

from backend.app.engine import Game, PatternRegistry


class GameStateTests(unittest.TestCase):
    def test_pattern_registry_contains_core_patterns(self):
        self.assertIn(PatternRegistry.SINGLE, PatternRegistry.all_patterns())
        self.assertIn(PatternRegistry.BOMB, PatternRegistry.all_patterns())

    def test_game_state_records_turn_log(self):
        game = Game(["你", "AI-1", "AI-2", "AI-3"])
        game.start_new_game()
        first_player = game.players[0]
        card = first_player.hand[0]
        game.play_turn(first_player, [card])
        self.assertGreaterEqual(len(game.state.log), 1)


if __name__ == "__main__":
    unittest.main()
