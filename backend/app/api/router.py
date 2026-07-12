"""游戏 HTTP 路由；规则交由现有游戏引擎，行为结果独立持久化。"""

from datetime import datetime
from time import perf_counter
from typing import Dict, Optional, Type

from fastapi import APIRouter, HTTPException

from ..engine.ai_player import Aggressive, Balanced, Conservative, RuleAIPlayer
from ..engine.card_type import identify_card_type
from ..engine.game import Game
from ..engine.personality_scoring import PersonalityScoringEngine
from ..engine.personality_titles import PersonalityTitleSystem
from ..database.sqlite import create_behavior_log, create_game_action_record, create_game_record, create_personality_score
from ..identity import AvatarProvider, NameProvider

from .schemas import (
    ActionResponse,
    GameResponse,
    HistoryResponse,
    PersonalityReportResponse,
    PlayRequest,
    RecommendRequest,
    RecommendResponse,
    StartGameRequest,
)


router = APIRouter(tags=["game"])
_game: Optional[Game] = None
_game_record_id: Optional[int] = None
_last_action_started: float = perf_counter()
_player_identities: Dict[str, Dict[str, str]] = {}


def _display_name(name: str) -> str:
    """把引擎内部稳定名称映射为本局随机展示昵称。"""
    return _player_identities.get(name, {}).get("name", name)


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
    for player in payload["players"]:
        identity = _player_identities.get(player["name"], {})
        player["engine_name"] = player["name"]
        player["name"] = identity.get("name", player["name"])
        player["avatar"] = identity.get("avatar", "")
        player["avatar_style"] = identity.get("avatar_style", "")
    payload["currentLevel"] = game.state.current_level
    player = _current_player(game)
    payload["current_hand"] = [card.to_dict() for card in player.hand]
    round_obj = game.current_round
    # 返回整局全部桌面动作；已经打出的牌始终留在牌桌记录中，直到新局开始。
    payload["state"]["table_plays"] = [] if round_obj is None else [
        {
            "player": _display_name(turn.player.name),
            "cards": [card.to_dict() for card in turn.cards],
            "is_pass": turn.is_pass,
        }
        for turn in round_obj.turn_history
    ]
    if payload["state"].get("last_player_name"):
        payload["state"]["last_player_name"] = _display_name(payload["state"]["last_player_name"])
    action_text = payload["state"].get("last_action_text")
    if action_text:
        for engine_name, identity in _player_identities.items():
            action_text = action_text.replace(engine_name, identity.get("name", engine_name))
        payload["state"]["last_action_text"] = action_text
    return payload


def _run_ai_until_human(game: Game) -> None:
    """自动推进 AI 回合，直到重新轮到真人或牌局结束。"""
    round_obj = game.current_round
    if round_obj is None:
        return

    # 正常情况下最多连续行动三名 AI；保留上限可避免损坏状态造成无限循环。
    for _ in range(12):
        if game.phase == "finished":
            return
        player = round_obj.players[round_obj.current_player_index]
        if player.is_human:
            return
        previous_player = round_obj.last_player
        started = perf_counter()
        turn = Balanced(game, player).play()
        if not turn.is_valid:
            raise RuntimeError(f"AI 出牌失败: {turn.message}")
        if _game_record_id is not None:
            decision_time = perf_counter() - started
            is_bomb = turn.pattern in {"bomb", "straight_flush", "joker_bomb"}
            partner_action = bool(previous_player and previous_player.team_id == player.team_id)
            detail = {
                "thinking_time_ms": round(decision_time * 1000, 3),
                "passed": turn.is_pass,
                "bomb_used": is_bomb,
                "helped_partner": turn.is_pass and partner_action,
                "partner_has_control": partner_action,
                "played_over_partner": not turn.is_pass and partner_action,
                "active_attack": previous_player is not None and not turn.is_pass,
                "critical_decision": len(player.hand) <= 8,
                "split_cards": False,
            }
            create_behavior_log(_game_record_id, player.name, "game_step", detail)
            create_game_action_record(
                str(_game_record_id), player.name, "pass" if turn.is_pass else ("bomb" if is_bomb else "play"),
                round_number=game.round_number,
                cards_played=str([str(card) for card in turn.cards]),
                card_type=turn.pattern,
                decision_time=round(decision_time, 4),
                opponent_cards=min((len(item.hand) for item in game.players if item.team_id != player.team_id), default=0),
                is_bomb=int(is_bomb),
                is_risky_play=0,
                partner_action=int(partner_action),
            )
    raise RuntimeError("AI 回合推进超过安全上限")


@router.post("/start_game", response_model=GameResponse)
def start_game(request: StartGameRequest) -> GameResponse:
    """创建并启动一局新的内存游戏。"""
    global _game, _game_record_id, _last_action_started, _player_identities
    if len(set(request.player_names)) != 4:
        raise HTTPException(status_code=422, detail="四名玩家名称不能重复")
    _game = Game(request.player_names)
    _game.start_new_game()
    ai_names = NameProvider().generate(3, excluded=[request.player_names[0]])
    ai_avatars = AvatarProvider().generate(3)
    _player_identities = {
        request.player_names[0]: {"name": request.player_names[0], "avatar": "", "avatar_style": ""},
        **{
            request.player_names[index]: {
                "name": ai_names[index - 1],
                "avatar": ai_avatars[index - 1]["url"],
                "avatar_style": ai_avatars[index - 1]["style"],
            }
            for index in range(1, 4)
        },
    }
    record = create_game_record(_game.to_dict())
    _game_record_id = record.id
    _last_action_started = perf_counter()
    return GameResponse(game=_game_payload(_game))


@router.post("/play", response_model=ActionResponse)
def play(request: PlayRequest) -> ActionResponse:
    """由当前玩家按手牌下标执行一次出牌。"""
    global _last_action_started
    game = _active_game()
    player = _current_player(game)
    thinking_time_ms = (perf_counter() - _last_action_started) * 1000
    previous_player = game.current_round.last_player if game.current_round else None
    if len(set(request.card_indices)) != len(request.card_indices):
        raise HTTPException(status_code=422, detail="手牌下标不能重复")
    if any(index < 0 or index >= len(player.hand) for index in request.card_indices):
        raise HTTPException(status_code=422, detail="手牌下标超出范围")
    cards = [player.hand[index] for index in request.card_indices]
    turn = game.play_turn(player, cards)
    if not turn.is_valid:
        raise HTTPException(status_code=400, detail=turn.message)
    game.check_winner()
    if _game_record_id is not None:
        opponent_cards = min(
            (len(item.hand) for item in game.players if item.team_id != player.team_id),
            default=0,
        )
        is_bomb = turn.pattern in {"bomb", "straight_flush", "joker_bomb"}
        create_behavior_log(
            _game_record_id,
            player.name,
            "game_step",
            {
                "thinking_time_ms": round(thinking_time_ms, 3),
                "passed": False,
                "bomb_used": is_bomb,
                "helped_partner": False,
                "partner_has_control": bool(previous_player and previous_player.team_id == player.team_id),
                "played_over_partner": bool(previous_player and previous_player.team_id == player.team_id),
                "active_attack": previous_player is not None,
                "critical_decision": len(player.hand) <= 8,
                "split_cards": False,
            },
        )
        create_game_action_record(
            str(_game_record_id), player.name, "bomb" if is_bomb else "play",
            round_number=game.round_number,
            cards_played=str([str(card) for card in cards]),
            card_type=turn.pattern,
            decision_time=round(thinking_time_ms / 1000, 4),
            opponent_cards=opponent_cards,
            is_bomb=int(is_bomb),
            is_risky_play=int((opponent_cards > 15 and is_bomb) or (opponent_cards < 5 and not is_bomb)),
            partner_action=int(bool(previous_player and previous_player.team_id == player.team_id)),
        )
    _run_ai_until_human(game)
    _last_action_started = perf_counter()
    return ActionResponse(turn=turn.to_dict(), game=_game_payload(game))


@router.post("/pass", response_model=ActionResponse)
def pass_turn() -> ActionResponse:
    """由当前玩家执行过牌；首家主动出牌时不允许过牌。"""
    global _last_action_started
    game = _active_game()
    round_obj = game.current_round
    if round_obj is None:
        raise HTTPException(status_code=409, detail="当前没有可用回合")
    if round_obj.last_played_cards is None:
        raise HTTPException(status_code=400, detail="当前拥有主动出牌权，不能过牌")
    player = _current_player(game)
    thinking_time_ms = (perf_counter() - _last_action_started) * 1000
    previous_player = round_obj.last_player
    turn = game.pass_turn(player)
    if not turn.is_valid:
        raise HTTPException(status_code=400, detail=turn.message)
    if _game_record_id is not None:
        create_behavior_log(
            _game_record_id,
            player.name,
            "game_step",
            {
                "thinking_time_ms": round(thinking_time_ms, 3),
                "passed": True,
                "bomb_used": False,
                "helped_partner": bool(previous_player and previous_player.team_id == player.team_id),
                "partner_has_control": bool(previous_player and previous_player.team_id == player.team_id),
                "yielded_control": bool(previous_player and previous_player.team_id == player.team_id),
                "critical_decision": len(player.hand) <= 8,
                "split_cards": False,
            },
        )
        create_game_action_record(
            str(_game_record_id), player.name, "pass",
            round_number=game.round_number,
            cards_played="[]",
            card_type="pass",
            decision_time=round(thinking_time_ms / 1000, 4),
            opponent_cards=min((len(item.hand) for item in game.players if item.team_id != player.team_id), default=0),
            is_bomb=0,
            is_risky_play=0,
            partner_action=int(bool(previous_player and previous_player.team_id == player.team_id)),
        )
    _run_ai_until_human(game)
    _last_action_started = perf_counter()
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
    for turn in turns:
        turn["player"] = _display_name(turn["player"])
    return HistoryResponse(logs=list(game.state.log), turns=turns)


@router.get("/personality_report", response_model=PersonalityReportResponse)
def personality_report() -> PersonalityReportResponse:
    """根据本局已采集行为生成并保存五维人格报告。"""
    game = _active_game()
    human = next((player for player in game.players if player.is_human), game.players[0])
    scorer = PersonalityScoringEngine()
    report = scorer.profile_for_player(human.name, _game_record_id)
    tags = report["tags"]
    personality_key = PersonalityTitleSystem.get_personality_key(*tags)
    personality_title = PersonalityTitleSystem.get_personality_data(personality_key)
    report.update({
        "player": {
            "name": _display_name(human.name),
            "avatar": _player_identities.get(human.name, {}).get("avatar", ""),
        },
        "summary": f"本局呈现出{'、'.join(tags)}的决策特征。建议结合多局数据观察稳定趋势。",
        "personality_key": personality_key,
        "personality_title": personality_title,
        "generated_at": datetime.utcnow().isoformat(),
    })
    if _game_record_id is not None:
        scores = report["scores"]
        create_personality_score(
            player_name=human.name,
            game_record_id=_game_record_id,
            aggression_score=scores["aggression"],
            cooperation_score=scores["cooperation"],
            emotion_score=scores["emotion"],
            risk_score=scores["risk"],
            decision_score=scores["decision"],
            personality_tags="|".join(tags),
        )
    return PersonalityReportResponse(report=report)
