from abc import ABC, abstractmethod
from typing import Any

from openai import AsyncOpenAI, APITimeoutError, APIError

from app.config import settings


class LLMClient(ABC):
    @abstractmethod
    async def chat_json(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        timeout: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Returns (parsed_json, error_message)."""


class OpenAILLMClient(LLMClient):
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key if api_key is not None else settings.openai_api_key
        self._client = AsyncOpenAI(api_key=key) if key else None

    async def chat_json(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        timeout: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if not self._client:
            return None, "OpenAI API key not configured"

        model_name = model or settings.openai_model
        timeout_sec = timeout if timeout is not None else settings.llm_timeout_seconds

        create_kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "timeout": timeout_sec,
        }
        if max_tokens is not None:
            create_kwargs["max_tokens"] = max_tokens

        try:
            response = await self._client.chat.completions.create(**create_kwargs)
        except APITimeoutError:
            return None, "LLM request timed out"
        except APIError as e:
            return None, f"LLM API error: {e.message if hasattr(e, 'message') else str(e)}"
        except Exception as e:
            return None, f"Unexpected LLM error: {e}"

        content = response.choices[0].message.content
        if not content:
            return None, "LLM returned empty content"

        import json

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None, "LLM returned malformed JSON"

        if not isinstance(parsed, dict):
            return None, "LLM JSON response is not an object"

        return parsed, None
