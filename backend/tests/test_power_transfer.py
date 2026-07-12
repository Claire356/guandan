"""三家连续 PASS 后牌权交接专项测试。"""

from backend.app.engine.card import Card
from backend.app.engine.game import Game
from backend.app.engine.player import Player
from backend.app.engine.power_transfer import PassCounter, PowerTransferStateMachine
from backend.app.engine.round import Round


def card(rank, suit="♠"):
    values = {"3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
    return Card(suit, rank, values[rank])


def prepared_round():
    players = [Player(f"玩家{index + 1}", team_id=index % 2) for index in range(4)]
    players[0].receive_cards([card("3"), card("K", "♠"), card("K", "♥")])
    players[1].receive_cards([card("4")])
    players[2].receive_cards([card("5")])
    players[3].receive_cards([card("6")])
    return players, Round(players)


def test_pass_counter_transfers_on_third_consecutive_pass():
    counter = PassCounter()
    counter.record_play(0)
    assert not counter.record_pass()
    assert not counter.record_pass()
    assert counter.record_pass()
    assert not counter.round_active


def test_three_passes_return_turn_to_last_player():
    players, round_obj = prepared_round()
    assert round_obj.play_turn(players[0], [players[0].hand[0]]).is_valid
    assert round_obj.play_turn(players[1], [], is_pass=True).is_valid
    assert round_obj.play_turn(players[2], [], is_pass=True).is_valid
    assert round_obj.play_turn(players[3], [], is_pass=True).is_valid
    assert round_obj.current_player_index == 0
    assert round_obj.last_played_cards is None
    assert round_obj.last_card_type is None
    assert round_obj.pass_counter.consecutive_passes == 0
    assert round_obj.last_power_transfer["player_name"] == "玩家1"


def test_power_holder_can_lead_a_different_card_type():
    players, round_obj = prepared_round()
    first = players[0].hand[0]
    round_obj.play_turn(players[0], [first])
    for player in players[1:]:
        round_obj.play_turn(player, [], is_pass=True)
    pair = list(players[0].hand)
    result = round_obj.play_turn(players[0], pair)
    assert result.is_valid
    assert result.pattern == "pair"


def test_power_holder_cannot_pass_before_new_lead():
    players, round_obj = prepared_round()
    round_obj.play_turn(players[0], [players[0].hand[0]])
    for player in players[1:]:
        round_obj.play_turn(player, [], is_pass=True)
    result = round_obj.play_turn(players[0], [], is_pass=True)
    assert not result.is_valid
    assert "不能PASS" in result.message


def test_any_valid_play_resets_pass_counter():
    players, round_obj = prepared_round()
    round_obj.play_turn(players[0], [players[0].hand[0]])
    round_obj.play_turn(players[1], [], is_pass=True)
    assert round_obj.pass_counter.consecutive_passes == 1
    result = round_obj.play_turn(players[2], [players[2].hand[0]])
    assert result.is_valid
    assert round_obj.pass_counter.consecutive_passes == 0


def test_game_state_and_log_include_power_transfer():
    game = Game(["玩家1", "玩家2", "玩家3", "玩家4"])
    game.start_new_game()
    round_obj = game.current_round
    round_obj.last_played_cards = [card("3")]
    round_obj.last_card_type = {"type": "single", "level": 3, "length": 1}
    round_obj.last_player = game.players[0]
    round_obj.pass_counter.record_play(0)
    round_obj.current_player_index = 1
    for index in (1, 2, 3):
        assert game.pass_turn(game.players[index]).is_valid
    assert game.state.current_player_index == 0
    assert game.state.power_holder_name == "玩家1"
    assert game.state.consecutive_passes == 0
    assert any("牌权交还给玩家1" in message for message in game.state.log)


def test_power_transfer_state_machine_cycle():
    machine = PowerTransferStateMachine()
    assert machine.on_play() == machine.WAITING_FOR_RESPONSE
    assert machine.on_pass(False) == machine.WAITING_FOR_RESPONSE
    assert machine.on_pass(True) == machine.ROUND_END
    assert machine.on_power_transfer() == machine.WAITING_FOR_PLAY
