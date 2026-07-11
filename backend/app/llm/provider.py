"""Provider 模式的统一 LLM 牌局分析接口。"""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional, TypedDict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .prompt import SYSTEM_PROMPT, build_analysis_prompt


class AnalysisResult(TypedDict):
    """所有 Provider 必须返回的统一 JSON 结构。"""

    summary: str
    mistake: str
    personality: str
    suggestion: str


class BaseProvider(ABC):
    """LLM Provider 抽象基类。"""

    required_fields = ("summary", "mistake", "personality", "suggestion")

    @abstractmethod
    def analyze(
        self,
        game: Any,
        behavior_scores: Mapping[str, float],
        personality: str,
    ) -> AnalysisResult:
        """分析牌局并返回统一结果。"""

    @classmethod
    def _parse_result(cls, content: str) -> AnalysisResult:
        """解析模型 JSON，并拒绝缺字段或非字符串结果。"""
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError("Provider 返回的内容不是有效 JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Provider 返回值必须是 JSON 对象")
        if set(cls.required_fields) - set(data):
            raise ValueError("Provider 返回值缺少统一字段")
        if any(not isinstance(data[field], str) for field in cls.required_fields):
            raise ValueError("Provider 返回字段必须全部为字符串")
        return {field: data[field] for field in cls.required_fields}  # type: ignore[return-value]


class OpenAICompatibleProvider(BaseProvider):
    """OpenAI Chat Completions 兼容协议的公共实现。"""

    provider_name = "compatible"
    api_key_env = "LLM_API_KEY"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv(self.api_key_env)
        self.model = model
        self.endpoint = endpoint
        self.timeout = timeout

    def _validate_configuration(self) -> None:
        """真实调用前检查配置，源码和错误信息均不会泄露 Key。"""
        if not self.api_key:
            raise RuntimeError(f"{self.provider_name} 尚未配置 API Key")
        if not self.model:
            raise RuntimeError(f"{self.provider_name} 尚未配置模型名称")
        if not self.endpoint:
            raise RuntimeError(f"{self.provider_name} 尚未配置接口地址")

    def _request(self, prompt: str) -> str:
        """使用标准库发送兼容请求，避免绑定特定厂商 SDK。"""
        self._validate_configuration()
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"{self.provider_name} 请求失败，HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"{self.provider_name} 网络连接失败") from exc
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"{self.provider_name} 响应结构无效") from exc

    def analyze(
        self,
        game: Any,
        behavior_scores: Mapping[str, float],
        personality: str,
    ) -> AnalysisResult:
        """构造统一 Prompt、调用模型并验证统一 JSON。"""
        prompt = build_analysis_prompt(game, behavior_scores, personality)
        return self._parse_result(self._request(prompt))


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI Provider；Key 和模型均通过参数或环境变量配置。"""

    provider_name = "OpenAI"
    api_key_env = "OPENAI_API_KEY"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, endpoint: Optional[str] = None, timeout: float = 60.0) -> None:
        super().__init__(
            api_key=api_key,
            model=model or os.getenv("OPENAI_MODEL"),
            endpoint=endpoint or os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
            timeout=timeout,
        )


class TongyiProvider(OpenAICompatibleProvider):
    """阿里云百炼/通义 Provider，使用其 OpenAI 兼容接口。"""

    provider_name = "Tongyi"
    api_key_env = "DASHSCOPE_API_KEY"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, endpoint: Optional[str] = None, timeout: float = 60.0) -> None:
        super().__init__(
            api_key=api_key,
            model=model or os.getenv("TONGYI_MODEL"),
            endpoint=endpoint or os.getenv("TONGYI_ENDPOINT", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"),
            timeout=timeout,
        )


class DoubaoProvider(OpenAICompatibleProvider):
    """火山方舟/豆包 Provider，使用其 OpenAI 兼容接口。"""

    provider_name = "Doubao"
    api_key_env = "ARK_API_KEY"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, endpoint: Optional[str] = None, timeout: float = 60.0) -> None:
        super().__init__(
            api_key=api_key,
            model=model or os.getenv("DOUBAO_MODEL"),
            endpoint=endpoint or os.getenv("DOUBAO_ENDPOINT", "https://ark.cn-beijing.volces.com/api/v3/chat/completions"),
            timeout=timeout,
        )


class MockProvider(BaseProvider):
    """无需 API 和网络的演示 Provider。"""

    def analyze(
        self,
        game: Any,
        behavior_scores: Mapping[str, float],
        personality: str,
    ) -> AnalysisResult:
        """根据已有评分生成稳定、可演示的本地结果。"""
        attack = float(behavior_scores.get("attack", 50.0))
        cooperation = float(behavior_scores.get("cooperation", 50.0))
        hesitation = float(behavior_scores.get("hesitation", 50.0))
        if hesitation >= 70:
            mistake = "关键回合思考偏久，可能错过更直接的出牌窗口。"
            suggestion = "提前整理可压制组合，并为关键牌型设置明确的出牌优先级。"
        elif attack >= 70:
            mistake = "进攻投入偏高，炸弹和高牌的使用时机仍可更克制。"
            suggestion = "出炸前比较剩余手牌收益，避免只为短期牌权消耗关键资源。"
        elif cooperation < 40:
            mistake = "对队友牌权和剩余手牌的配合关注不足。"
            suggestion = "队友掌握主动权时减少无必要压制，优先保留接应牌。"
        else:
            mistake = "整体决策较稳定，但部分回合仍可提高牌序规划效率。"
            suggestion = "继续保持均衡策略，并在残局前预先规划两到三手出牌路径。"
        return {
            "summary": "已完成本局牌序、行为评分和关键决策的规则化复盘。",
            "mistake": mistake,
            "personality": f"本局表现与“{personality}”特征基本一致。",
            "suggestion": suggestion,
        }


__all__ = [
    "AnalysisResult",
    "BaseProvider",
    "OpenAIProvider",
    "TongyiProvider",
    "DoubaoProvider",
    "MockProvider",
]
