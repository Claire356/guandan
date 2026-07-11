import unittest
from collections import Counter

from backend.app.engine.ai_player import Aggressive, Balanced, Conservative
from backend.app.engine.card_type import identify_card_type
from backend.app.engine.game import Game


class AIPlayerTests(unittest.TestCase):
    def test_ai_interfaces_and_twenty_game_simulation(self):
        wins = Counter()
        styles = [Aggressive, Balanced, Conservative, Balanced]

        for game_index in range(20):
            game = Game(["Aggressive", "Balanced-A", "Conservative", "Balanced-B"])
            game.start_new_game()
            # 轮换策略座位，避免固定首家位置影响统计。
            rotated = styles[game_index % 4:] + styles[:game_index % 4]
            agents = {
                player: strategy(game, player)
                for player, strategy in zip(game.players, rotated)
            }

            for _ in range(2000):
                if game.winner is not None:
                    break
                current = game.current_round.players[game.current_round.current_player_index]
                turn = agents[current].play()
                self.assertTrue(turn.is_valid)
            self.assertIsNotNone(game.winner, f"第 {game_index + 1} 局未在限制步数内结束")
            wins[agents[game.winner].style] += 1

        self.assertEqual(sum(wins.values()), 20)
        print("\n20局AI模拟胜率统计")
        for style in ("aggressive", "balanced", "conservative"):
            count = wins[style]
            print(f"{style}: {count}/20 ({count / 20:.1%})")

    def test_recommend_returns_cards_from_hand(self):
        game = Game()
        game.start_new_game()
        ai = Balanced(game, game.players[0])
        recommendation = ai.recommend()
        self.assertTrue(recommendation)
        self.assertTrue(all(card in ai.player.hand for card in recommendation))
        self.assertNotEqual(identify_card_type(recommendation)["type"], "invalid")

    def test_choose_bomb_and_pass_are_callable(self):
        game = Game()
        game.start_new_game()
        ai = Conservative(game, game.players[0])
        self.assertIsInstance(ai.chooseBomb(), list)
        self.assertIsInstance(ai.choosePass(), bool)


if __name__ == "__main__":
    unittest.main()
