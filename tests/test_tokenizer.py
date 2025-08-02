from unittest.mock import MagicMock, patch

import app.agents as agents


def test_log_metrics_uses_tiktoken(monkeypatch):
    enc = MagicMock()
    enc.encode.return_value = [1, 2]
    fake_tk = MagicMock(get_encoding=lambda name: enc)
    monkeypatch.setattr(agents, "tokenizer", fake_tk)
    with patch.object(
        agents.run_helpers, "get_current_run_tree", return_value=None
    ), patch.object(agents, "logger") as log:
        agents._log_metrics("token", 1)
    enc.encode.assert_called_once_with("token")
    assert log.info.call_args[0][1] == 2


def test_log_metrics_falls_back_without_tiktoken(monkeypatch):
    monkeypatch.setattr(agents, "tokenizer", None)
    fake_run = MagicMock()
    with patch.object(
        agents.run_helpers, "get_current_run_tree", return_value=fake_run
    ), patch.object(agents, "logger"):
        agents._log_metrics("two words", 0)
    event = fake_run.add_event.call_args[0][0]
    assert event["kwargs"]["token_count"] == 2
