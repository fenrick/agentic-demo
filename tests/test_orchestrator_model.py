import importlib

import tiktoken

import config


def test_orchestrator_allows_custom_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("MODEL", "openai:gpt-5-mini")

    # ensure config reloads with new environment
    importlib.reload(config)
    config.load_settings.cache_clear()

    called = {}

    def fake_encoding_for_model(name: str):  # pragma: no cover - simple stub
        called["name"] = name

        class Dummy:
            def encode(self, text: str) -> list[int]:  # pragma: no cover - stub
                return []

        return Dummy()

    monkeypatch.setattr(tiktoken, "encoding_for_model", fake_encoding_for_model)
    monkeypatch.setattr(tiktoken, "get_encoding", fake_encoding_for_model)

    import core.orchestrator as orchestrator

    importlib.reload(orchestrator)

    assert called["name"] == "gpt-5-mini"
    assert orchestrator.config.load_settings().model == "openai:gpt-5-mini"
