"""五维人格称号系统完整性测试。"""

from itertools import product

from backend.app.engine.personality_titles import PersonalityTitleSystem


def test_all_thirty_two_personality_combinations_exist():
    expected = {
        "-".join(items)
        for items in product(("侵", "保"), ("合", "独"), ("情", "冷"), ("赌", "稳"), ("果", "犹"))
    }
    assert set(PersonalityTitleSystem.PERSONALITY_DATABASE) == expected


def test_full_chinese_tags_map_to_expected_key():
    key = PersonalityTitleSystem.get_personality_key("侵略型", "合作型", "冷静型", "稳健型", "果断型")
    assert key == "侵-合-冷-稳-果"
    assert PersonalityTitleSystem.get_personality_data(key)["title"] == "特种兵指挥官"


def test_every_title_has_complete_report_fields():
    required = {"title", "emoji", "psychology", "playstyle", "catchphrase", "tags", "warning"}
    for data in PersonalityTitleSystem.PERSONALITY_DATABASE.values():
        assert required <= set(data)
        assert len(data["tags"]) >= 1


def test_unknown_key_returns_safe_default():
    assert PersonalityTitleSystem.get_personality_data("unknown")["title"] == "未定义的神秘人"
