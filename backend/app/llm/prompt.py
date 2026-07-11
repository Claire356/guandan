"""LLM 分析提示词；业务方可只修改本文件调整分析风格。"""

import json
from typing import Any, Mapping


SYSTEM_PROMPT = """你是一名专业的掼蛋复盘教练。
请依据牌局、五维行为评分和人格类型给出简洁、具体、可执行的复盘。
不得编造输入中不存在的牌局事实。
必须只输出一个 JSON 对象，不要使用 Markdown，不要添加额外说明。
JSON 必须严格包含以下字符串字段：summary、mistake、personality、suggestion。
"""


ANALYSIS_TEMPLATE = """请分析以下数据：

牌局：
{game}

行为评分：
{behavior_scores}

人格：
{personality}

只返回以下结构：
{{
  "summary": "牌局总结",
  "mistake": "主要问题",
  "personality": "人格表现分析",
  "suggestion": "改进建议"
}}
"""


def build_analysis_prompt(
    game: Any,
    behavior_scores: Mapping[str, float],
    personality: str,
) -> str:
    """把三类输入序列化后填入统一分析模板。"""
    game_data = game.to_dict() if hasattr(game, "to_dict") else game
    return ANALYSIS_TEMPLATE.format(
        game=json.dumps(game_data, ensure_ascii=False, default=str, indent=2),
        behavior_scores=json.dumps(dict(behavior_scores), ensure_ascii=False, indent=2),
        personality=personality,
    )


__all__ = ["SYSTEM_PROMPT", "ANALYSIS_TEMPLATE", "build_analysis_prompt"]
