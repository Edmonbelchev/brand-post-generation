from typing import Any

from app.llm.client import LLMClient


class MockLLMClient(LLMClient):
    def __init__(
        self,
        generate_response: tuple[dict[str, Any] | None, str | None] | None = None,
        evaluate_response: tuple[dict[str, Any] | None, str | None] | None = None,
    ) -> None:
        self.generate_response = generate_response
        self.evaluate_response = evaluate_response
        self.generate_calls = 0
        self.evaluate_calls = 0
        self._call_index = 0

    async def chat_json(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        timeout: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        sys_lower = system.lower()
        is_evaluator = (
            "you score how well copy matches" in sys_lower
            or "score rubric" in sys_lower
            or ("brand voice" in sys_lower and '"score"' in system)
        )
        if is_evaluator:
            self.evaluate_calls += 1
            if self.evaluate_response is not None:
                return self.evaluate_response
            return {"score": 90, "feedback": []}, None

        self.generate_calls += 1
        if self.generate_response is not None:
            return self.generate_response
        return {"post": "Fresh beans, roasted this week. That is the whole story."}, None


class SequenceLLMClient(LLMClient):
    """Returns different responses per call in order."""

    def __init__(self, responses: list[tuple[dict[str, Any] | None, str | None]]) -> None:
        self.responses = responses
        self.index = 0

    async def chat_json(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        timeout: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if self.index >= len(self.responses):
            return None, "No more mocked responses"
        resp = self.responses[self.index]
        self.index += 1
        return resp
