"""游戏 HTTP 路由；仅保存内存状态，不使用数据库。"""

from typing import Dict, Optional, Type

from fastapi import APIRouter, HTTPException

from ..engine.ai_player import Aggressive, Balanced, Conservative, RuleAIPlayer
from ..engine.card_type import identify_card_type
from ..engine.game import Game

from .schemas import (
    ActionResponse,
    GameResponse,
    HistoryResponse,
    PlayRequest,
    RecommendRequest,
    RecommendResponse,
    StartGameRequest,
)


router = APIRouter(tags=["game"])
_game: Optional[Game] = None


def _active_game() -> Game:
    """返回当前内存游戏；尚未开始时给出统一 HTTP 错误。"""
    if _game is None or _game.current_round is None:
        raise HTTPException(status_code=409, detail="游戏尚未开始，请先调用 /start_game")
    return _game


def _current_player(game: Game):
    """取得当前应行动的玩家。"""
    round_obj = game.current_round
    if round_obj is None:
        raise HTTPException(status_code=409, detail="当前没有可用回合")
    return round_obj.players[round_obj.current_player_index]


def _game_payload(game: Game) -> dict:
    """返回游戏状态，并附带当前行动玩家的真实手牌。"""
    payload = game.to_dict()
    payload["currentLevel"] = game.state.current_level
    player = _current_player(game)
    payload["current_hand"] = [card.to_dict() for card in player.hand]
    round_obj = game.current_round
    # 返回整局全部桌面动作；已经打出的牌始终留在牌桌记录中，直到新局开始。
    payload["state"]["table_plays"] = [] if round_obj is None else [
        {
            "player": turn.player.name,
            "cards": [card.to_dict() for card in turn.cards],
            "is_pass": turn.is_pass,
        }
        for turn in round_obj.turn_history
    ]
    return payload


def _run_ai_until_human(game: Game) -> None:
    """自动推进 AI 回合，直到重新轮到真人或牌局结束。"""
    round_obj = game.current_round
    if round_obj is None:
        return

    # 正常情况下最多连续行动三名 AI；保留上限可避免损坏状态造成无限循环。
    for _ in range(12):
        if game.winner is not None:
            return
        player = round_obj.players[round_obj.current_player_index]
        if player.is_human:
            return
        turn = Balanced(game, player).play()
        if not turn.is_valid:
            raise RuntimeError(f"AI 出牌失败: {turn.message}")
    raise RuntimeError("AI 回合推进超过安全上限")


@router.post("/start_game", response_model=GameResponse)
def start_game(request: StartGameRequest) -> GameResponse:
    """创建并启动一局新的内存游戏。"""
    global _game
    if len(set(request.player_names)) != 4:
        raise HTTPException(status_code=422, detail="四名玩家名称不能重复")
    _game = Game(request.player_names)
    _game.start_new_game()
    return GameResponse(game=_game_payload(_game))


@router.post("/play", response_model=ActionResponse)
def play(request: PlayRequest) -> ActionResponse:
    """由当前玩家按手牌下标执行一次出牌。"""
    game = _active_game()
    player = _current_player(game)
    if len(set(request.card_indices)) != len(request.card_indices):
        raise HTTPException(status_code=422, detail="手牌下标不能重复")
    if any(index < 0 or index >= len(player.hand) for index in request.card_indices):
        raise HTTPException(status_code=422, detail="手牌下标超出范围")
    cards = [player.hand[index] for index in request.card_indices]
    turn = game.play_turn(player, cards)
    if not turn.is_valid:
        raise HTTPException(status_code=400, detail=turn.message)
    game.check_winner()
    _run_ai_until_human(game)
    return ActionResponse(turn=turn.to_dict(), game=_game_payload(game))


@router.post("/pass", response_model=ActionResponse)
def pass_turn() -> ActionResponse:
    """由当前玩家执行过牌；首家主动出牌时不允许过牌。"""
    game = _active_game()
    round_obj = game.current_round
    if round_obj is None:
        raise HTTPException(status_code=409, detail="当前没有可用回合")
    if round_obj.last_played_cards is None:
        raise HTTPException(status_code=400, detail="当前拥有主动出牌权，不能过牌")
    player = _current_player(game)
    turn = round_obj.play_turn(player, [], is_pass=True)
    game.state.current_player_index = round_obj.current_player_index
    game.state.current_turn_count += 1
    game.state.add_log(f"{player.name} 选择PASS")
    if len(round_obj.turn_history) >= 3 and all(item.is_pass for item in round_obj.turn_history[-3:]):
        round_obj.last_played_cards = None
        round_obj.last_player = None
        round_obj.phase = "waiting"
        game.state.last_played_cards = None
        game.state.last_player_name = None
    _run_ai_until_human(game)
    return ActionResponse(turn=turn.to_dict(), game=_game_payload(game))


@router.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> RecommendResponse:
    """为当前玩家生成规则推荐，但不修改游戏状态。"""
    game = _active_game()
    player = _current_player(game)
    strategies: Dict[str, Type[RuleAIPlayer]] = {
        "aggressive": Aggressive,
        "balanced": Balanced,
        "conservative": Conservative,
    }
    ai = strategies[request.strategy](game, player)
    recommendation = ai.recommend_with_reason()
    cards = recommendation["recommend_cards"]
    return RecommendResponse(
        should_pass=not cards,
        cards=[card.to_dict() for card in cards],
        recommend_cards=[card.to_dict() for card in cards],
        card_type=identify_card_type(cards, game.state.current_level),
        reason=recommendation["reason"],
        expected_value=recommendation["expected_value"],
    )


@router.get("/history", response_model=HistoryResponse)
def history() -> HistoryResponse:
    """返回当前游戏的状态日志与完整回合历史。"""
    game = _active_game()
    round_obj = game.current_round
    turns = [] if round_obj is None else [turn.to_dict() for turn in round_obj.turn_history]
    return HistoryResponse(logs=list(game.state.log), turns=turns)
