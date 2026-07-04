from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMProvider:
    """Abstract base class for LLM providers."""

    def complete(
        self, *, model: str, messages: list[dict], temperature: float = 0.2
    ) -> LLMResponse:
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible chat completions provider."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.environ["OPENAI_API_KEY"]
        self.base_url = (
            base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        ).rstrip("/")

    def complete(
        self, *, model: str, messages: list[dict], temperature: float = 0.2
    ) -> LLMResponse:
        payload = {"model": model, "messages": messages, "temperature": temperature}
        with httpx.Client(timeout=120) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )


class MockProvider(LLMProvider):
    """Mock provider for tests. Returns predefined responses in order."""

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.calls: list[dict] = []

    def complete(
        self, *, model: str, messages: list[dict], temperature: float = 0.2
    ) -> LLMResponse:
        self.calls.append(
            {"model": model, "messages": messages, "temperature": temperature}
        )
        text = self.responses.pop(0)
        return LLMResponse(text=text, input_tokens=100, output_tokens=50)
