import json
import unittest

from backend.app.database.sqlite import BehaviorLog
from backend.app.engine.personality_scoring import PersonalityScoringEngine


def behavior_log(**detail):
    defaults = {
        "thinking_time_ms": 1000,
        "passed": False,
        "bomb_used": False,
        "bombs_retained": 0,
        "helped_partner": False,
        "split_cards": False,
        "recommendation_clicked": False,
        "critical_decision": False,
    }
    defaults.update(detail)
    return BehaviorLog(
        id=1,
        game_record_id=1,
        player_name="测试玩家",
        behavior_type="game_step",
        detail_json=json.dumps(defaults),
    )


class PersonalityScoringTests(unittest.TestCase):
    def test_pass_adds_two_hesitation_points(self):
        engine = PersonalityScoringEngine()
        result = engine.score_logs([behavior_log(passed=True)])
        self.assertEqual(result["hesitation"], 52.0)

    def test_critical_bomb_adds_eight_attack_points_in_event(self):
        engine = PersonalityScoringEngine()
        events = engine._events_from_detail({"bomb_used": True, "critical_decision": True, "thinking_time_ms": 5000})
        self.assertIn("critical_bomb", events)
        self.assertEqual(engine.event_weights["critical_bomb"]["attack"], 8.0)

    def test_helping_partner_adds_ten_cooperation_points(self):
        engine = PersonalityScoringEngine()
        result = engine.score_logs([behavior_log(helped_partner=True)])
        self.assertEqual(result["cooperation"], 60.0)

    def test_over_fifteen_seconds_adds_five_hesitation_points(self):
        engine = PersonalityScoringEngine()
        result = engine.score_logs([behavior_log(thinking_time_ms=16000)])
        self.assertEqual(result["hesitation"], 55.0)

    def test_scores_are_clamped_to_zero_and_one_hundred(self):
        engine = PersonalityScoringEngine()
        result = engine.score_logs([behavior_log(bomb_used=True, critical_decision=True)] * 20)
        self.assertTrue(all(0 <= value <= 100 for value in result.values()))

    def test_output_has_exact_five_dimensions(self):
        self.assertEqual(
            set(PersonalityScoringEngine().result()),
            {"attack", "cooperation", "risk", "hesitation", "emotion"},
        )

    def test_recommendation_click_log_counts_once(self):
        engine = PersonalityScoringEngine()
        click = BehaviorLog(
            id=2,
            game_record_id=1,
            player_name="测试玩家",
            behavior_type="recommendation_click",
            detail_json="{}",
        )
        result = engine.score_logs([click])
        self.assertEqual(result["hesitation"], 51.0)

    def test_all_seven_personality_mappings(self):
        engine = PersonalityScoringEngine()
        cases = [
            ({"attack": 80, "cooperation": 50, "risk": 70, "hesitation": 50, "emotion": 50}, "激进冲锋型"),
            ({"attack": 30, "cooperation": 50, "risk": 30, "hesitation": 50, "emotion": 50}, "保守隐忍型"),
            ({"attack": 50, "cooperation": 80, "risk": 50, "hesitation": 50, "emotion": 50}, "团队协作型"),
            ({"attack": 50, "cooperation": 50, "risk": 70, "hesitation": 50, "emotion": 75}, "城府伪装型"),
            ({"attack": 50, "cooperation": 50, "risk": 50, "hesitation": 80, "emotion": 50}, "纠结犹豫型"),
            ({"attack": 50, "cooperation": 50, "risk": 50, "hesitation": 50, "emotion": 20}, "情绪化型"),
            ({"attack": 50, "cooperation": 50, "risk": 50, "hesitation": 50, "emotion": 50}, "均衡稳健型"),
        ]
        for scores, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(engine.personality(scores), expected)


if __name__ == "__main__":
    unittest.main()
