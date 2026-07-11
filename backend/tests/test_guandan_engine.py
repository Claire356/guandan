import unittest

from backend.app.engine import Card, Deck, Player, Game, Round


class GuandanEngineTests(unittest.TestCase):
    def test_deck_contains_108_cards(self):
        deck = Deck()
        self.assertEqual(len(deck.cards), 108)

    def test_shuffle_changes_order(self):
        deck = Deck()
        original = list(deck.cards)
        deck.shuffle()
        self.assertEqual(len(deck.cards), 108)
        self.assertNotEqual([card.to_dict() for card in deck.cards], [card.to_dict() for card in original])

    def test_game_deals_cards_to_players(self):
        game = Game(player_names=["你", "AI-1", "AI-2", "AI-3"])
        game.start_new_game()
        for player in game.players:
            self.assertEqual(len(player.hand), 27)

    def test_round_can_accept_single_card_play(self):
        game = Game(player_names=["你", "AI-1", "AI-2", "AI-3"])
        game.start_new_game()
        first_player = game.players[0]
        card = first_player.hand[0]
        turn = game.current_round.play_turn(first_player, [card])
        self.assertTrue(turn.is_valid)
        self.assertEqual(turn.pattern, "single")

    def test_bomb_can_beat_single_card(self):
        player_a = Player("A")
        player_b = Player("B")
        round_obj = Round([player_a, player_b])
        single_card = Card(suit="♠", rank="3", value=3, is_joker=False)
        bomb_cards = [
            Card(suit="♠", rank="4", value=4, is_joker=False),
            Card(suit="♥", rank="4", value=4, is_joker=False),
            Card(suit="♣", rank="4", value=4, is_joker=False),
            Card(suit="♦", rank="4", value=4, is_joker=False),
        ]
        player_a.receive_cards([single_card])
        player_b.receive_cards(bomb_cards)
        round_obj.play_turn(player_a, [single_card])
        turn = round_obj.play_turn(player_b, bomb_cards)
        self.assertTrue(turn.is_valid)
        self.assertEqual(turn.pattern, "bomb")

    def test_player_can_give_and_return_contribution(self):
        player = Player("A")
        card = Card(suit="♠", rank="2", value=15, is_joker=False)
        player.receive_cards([card])
        player.give_contribution([card])
        self.assertEqual(len(player.contributions), 1)
        player.return_contribution([card])
        self.assertEqual(len(player.hand), 1)


if __name__ == "__main__":
    unittest.main()
