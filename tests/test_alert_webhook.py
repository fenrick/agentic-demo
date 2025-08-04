from pathlib import Path
from typing import Any, Dict

import httpx

from metrics.alerts import AlertManager, AlertSummary
from metrics.repository import MetricsRepository


def test_send_webhook_posts_payload(monkeypatch, tmp_path: Path) -> None:
    captured: Dict[str, Any] = {}

    def fake_post(url: str, json: Dict[str, Any], timeout: float) -> httpx.Response:  # type: ignore[override]
        captured["url"] = url
        captured["json"] = json
        return httpx.Response(200)

    monkeypatch.setattr(httpx, "post", fake_post)

    repo = MetricsRepository(str(tmp_path / "metrics.db"))
    manager = AlertManager(
        repo,
        thresholds_path=Path("src/config/thresholds.yaml"),
        webhook_url="http://example.com",
    )
    alert = AlertSummary(
        workspace_id="ws1",
        pedagogical_score=0.8,
        hallucination_rate=0.03,
        cost=0.7,
        pedagogical_breached=True,
        hallucination_breached=False,
        cost_breached=True,
    )

    manager.send_webhook(alert)

    assert captured["url"] == "http://example.com"
    assert captured["json"]["workspace_id"] == "ws1"
    breaches = captured["json"]["breaches"]
    assert "pedagogical_score" in breaches
    assert "cost" in breaches
    assert "hallucination_rate" not in breaches
