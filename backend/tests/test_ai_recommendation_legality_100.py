import random
import unittest

from backend.app.engine.ai_player import Aggressive, Balanced, Conservative
from backend.app.engine.game import Game
from backend.app.engine.validator import validate_play


class AIRecommendationLegality100GamesTests(unittest.TestCase):
    def test_100_games_every_recommendation_is_legal(self):
        """100局中每次非PASS推荐都必须通过validate_play→compare链路。"""
        random.seed(20260712)
        strategies = [Aggressive, Balanced, Conservative, Balanced]
        checked_recommendations = 0

        for game_index in range(100):
            game = Game(["Aggressive", "Balanced-A", "Conservative", "Balanced-B"])
            game.start_new_game()
            rotated = strategies[game_index % 4:] + strategies[:game_index % 4]
            agents = {player: strategy(game, player) for player, strategy in zip(game.players, rotated)}

            for turn_index in range(2000):
                if game.winner is not None:
                    break
                round_obj = game.current_round
                player = round_obj.players[round_obj.current_player_index]
                ai = agents[player]
                table_type = round_obj.last_card_type
                recommendation = ai.recommend(table_type)

                if recommendation:
                    validation = validate_play(player.hand, table_type, recommendation, game.state.current_level)
                    self.assertTrue(
                        validation["valid"],
                        f"第{game_index + 1}局第{turn_index + 1}手非法推荐: "
                        f"桌面={table_type}, 推荐={[str(card) for card in recommendation]}, "
                        f"原因={validation['reason']}",
                    )
                    self.assertTrue(any(recommendation == move for move in ai.last_legal_moves))
                    checked_recommendations += 1
                    turn = game.play_turn(player, recommendation)
                    self.assertTrue(turn.is_valid)
                    game.check_winner()
                else:
                    self.assertIsNotNone(table_type, "拥有主动出牌权时AI不能推荐PASS")
                    turn = round_obj.play_turn(player, [], is_pass=True)
                    self.assertTrue(turn.is_valid)
                    game.state.current_player_index = round_obj.current_player_index
                    if len(round_obj.turn_history) >= 3 and all(item.is_pass for item in round_obj.turn_history[-3:]):
                        round_obj.last_played_cards = None
                        round_obj.last_card_type = None
                        round_obj.last_player = None
                        game.state.last_played_cards = None
                        game.state.last_player_name = None
            else:
                self.fail(f"第{game_index + 1}局超过最大步数")

        self.assertGreater(checked_recommendations, 1000)


if __name__ == "__main__":
    unittest.main()
