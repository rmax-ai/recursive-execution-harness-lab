from __future__ import annotations

from rxh.providers import MockProvider, OpenAICompatibleProvider


def test_mock_provider_returns_responses_in_order() -> None:
    provider = MockProvider(["first", "second"])

    first = provider.complete(
        model="gpt-test", messages=[{"role": "user", "content": "a"}]
    )
    second = provider.complete(
        model="gpt-test", messages=[{"role": "user", "content": "b"}]
    )

    assert first.text == "first"
    assert second.text == "second"


def test_mock_provider_tracks_calls() -> None:
    provider = MockProvider(["ok"])
    messages = [{"role": "user", "content": "hello"}]

    provider.complete(model="model-x", messages=messages, temperature=0.1)

    assert provider.calls == [
        {"model": "model-x", "messages": messages, "temperature": 0.1}
    ]


def test_openai_compatible_provider_init_with_explicit_key_and_url(
    monkeypatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example/v1")

    provider = OpenAICompatibleProvider(
        api_key="explicit-key", base_url="https://api.example/v1/"
    )

    assert provider.api_key == "explicit-key"
    assert provider.base_url == "https://api.example/v1"
