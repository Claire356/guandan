import json
import unittest

from backend.app.llm.prompt import build_analysis_prompt
from backend.app.llm.provider import (
    DoubaoProvider,
    MockProvider,
    OpenAIProvider,
    TongyiProvider,
)


class LLMProviderTests(unittest.TestCase):
    def test_mock_provider_returns_unified_json(self):
        result = MockProvider().analyze(
            {"winner": "AI-1"},
            {"attack": 75, "cooperation": 50, "risk": 70, "hesitation": 40, "emotion": 60},
            "激进冲锋型",
        )
        self.assertEqual(set(result), {"summary", "mistake", "personality", "suggestion"})
        self.assertTrue(all(isinstance(value, str) for value in result.values()))

    def test_prompt_contains_all_inputs(self):
        prompt = build_analysis_prompt({"phase": "finished"}, {"attack": 60}, "均衡稳健型")
        self.assertIn("finished", prompt)
        self.assertIn("attack", prompt)
        self.assertIn("均衡稳健型", prompt)

    def test_real_providers_have_no_embedded_key(self):
        for provider in (OpenAIProvider(), TongyiProvider(), DoubaoProvider()):
            self.assertFalse(provider.api_key)

    def test_missing_api_key_fails_clearly(self):
        with self.assertRaisesRegex(RuntimeError, "API Key"):
            OpenAIProvider(model="example-model").analyze({}, {}, "均衡稳健型")

    def test_json_code_fence_can_be_parsed(self):
        content = "```json\n" + json.dumps({
            "summary": "总结",
            "mistake": "问题",
            "personality": "人格",
            "suggestion": "建议",
        }, ensure_ascii=False) + "\n```"
        result = MockProvider._parse_result(content)
        self.assertEqual(result["summary"], "总结")


if __name__ == "__main__":
    unittest.main()
