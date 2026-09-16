from pathlib import Path


def _enriched():
    return {"trades": [], "institutional": [], "crypto": []}


def test_summarize_uses_configured_nvidia_provider(monkeypatch):
    from digest import summarizer

    calls = {}

    class FakeCompletions:
        def create(self, **kwargs):
            calls["create_kwargs"] = kwargs

            class Message:
                content = '{"entity_summaries": [], "macro_note": "x"}'

            class Choice:
                message = Message()

            class Response:
                choices = [Choice()]

            return Response()

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            calls["client_kwargs"] = kwargs
            self.chat = FakeChat()

    monkeypatch.setattr(summarizer, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        summarizer,
        "PROVIDERS",
        (("nvidia/nemotron-3-super-120b-a12b", summarizer.NVIDIA_BASE_URL, "test-key"),),
    )

    result = summarizer.summarize(_enriched(), {}, "2026-01-01", "2026-01-07")

    assert calls["client_kwargs"] == {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": "test-key",
        "timeout": summarizer.REQUEST_TIMEOUT_S,
        "max_retries": 0,
    }
    assert calls["create_kwargs"]["model"] == "nvidia/nemotron-3-super-120b-a12b"
    assert calls["create_kwargs"]["response_format"] == {"type": "json_object"}
    assert set(result) >= {"entity_summaries", "macro_note"}


def test_summarize_skips_unconfigured_provider_and_uses_fallback(monkeypatch):
    from digest import summarizer

    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs["model"])

            class Message:
                content = '{"entity_summaries": [], "macro_note": "fallback"}'

            class Choice:
                message = Message()

            class Response:
                choices = [Choice()]

            return Response()

    class FakeOpenAI:
        def __init__(self, **_kwargs):
            self.chat = type("FakeChat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr(summarizer, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        summarizer,
        "PROVIDERS",
        (
            ("gemini-primary", summarizer.GEMINI_BASE_URL, ""),
            ("nvidia-fallback", summarizer.NVIDIA_BASE_URL, "test-key"),
        ),
    )

    result = summarizer.summarize(_enriched(), {}, "2026-01-01", "2026-01-07")

    assert calls == ["nvidia-fallback"]
    assert result["macro_note"] == "fallback"


def test_summarize_raises_clear_error_on_empty_completion(monkeypatch):
    import pytest

    from digest import summarizer

    class FakeCompletions:
        def create(self, **_kwargs):
            class Message:
                content = None

            class Choice:
                message = Message()
                finish_reason = "stop"

            class Response:
                choices = [Choice()]

            return Response()

    class FakeOpenAI:
        def __init__(self, **_kwargs):
            self.chat = type("FakeChat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr(summarizer, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(summarizer, "PROVIDERS", (("test-model", "https://example.test", "test-key"),))
    monkeypatch.setattr(summarizer, "ATTEMPTS", 1)

    with pytest.raises(RuntimeError, match="Empty completion"):
        summarizer.summarize(_enriched(), {}, "2026-01-01", "2026-01-07")


def test_summarizer_source_uses_nvidia_endpoint():
    source = Path("digest/summarizer.py").read_text()
    assert "https://integrate.api.nvidia.com/v1" in source
