"""身份 Provider 与新版五维画像测试；不触碰牌局规则。"""

import json
import random

from sqlalchemy import inspect

from backend.app.database.sqlite import BehaviorLog, engine, init_db
from backend.app.engine.personality_scoring import PersonalityScoringEngine
from backend.app.identity import AvatarProvider, NameProvider


def _log(**detail):
    return BehaviorLog(
        id=1,
        game_record_id=1,
        player_name="你",
        behavior_type="game_step",
        detail_json=json.dumps(detail),
    )


def test_avatar_provider_returns_unique_500_square_portraits():
    avatars = AvatarProvider(random.Random(7)).generate(3)
    assert len({item["url"] for item in avatars}) == 3
    assert all(item["width"] == 500 and item["height"] == 500 for item in avatars)


def test_name_provider_returns_unique_short_names():
    names = NameProvider(random.Random(7)).generate(3, excluded=["牌圣"])
    assert len(set(names)) == 3
    assert "牌圣" not in names
    assert all(len(name) <= 5 for name in names)


def test_profile_uses_fifty_as_configured_baseline():
    profile = PersonalityScoringEngine().profile_logs([])
    assert set(profile["scores"]) == {"aggression", "cooperation", "emotion", "risk", "decision"}
    assert all(score == 50 for score in profile["scores"].values())


def test_fast_bomb_increases_aggression_risk_and_decision():
    profile = PersonalityScoringEngine().profile_logs([
        _log(thinking_time_ms=2000, bomb_used=True, critical_decision=True, risky_play=True,
             early_big_card=True, late_small_card=True, high_card_used=True, split_cards=True)
    ])
    assert profile["scores"]["aggression"] > 50
    assert profile["scores"]["risk"] > 50
    assert profile["scores"]["decision"] > 50


def test_profile_contains_five_tags_and_explanations():
    profile = PersonalityScoringEngine().profile_logs([])
    assert len(profile["tags"]) == 5
    assert all(item["explanation"] for item in profile["dimensions"])


def test_attachment_behavior_tables_are_created_automatically():
    init_db()
    tables = set(inspect(engine).get_table_names())
    assert {"game_records", "player_statistics"} <= tables


def test_percentile_rank_has_neutral_empty_population():
    engine_instance = PersonalityScoringEngine()
    assert engine_instance.percentile_rank(10, []) == 0.5
    assert engine_instance.percentile_rank(2, [1, 2, 3, 4]) == 0.5
