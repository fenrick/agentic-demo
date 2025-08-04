"""Threshold alert evaluation and webhook dispatch."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import httpx
import yaml  # type: ignore[import-untyped]

from .repository import MetricsRepository


@dataclass
class AlertSummary:
    """Result of threshold evaluation for a workspace."""

    workspace_id: str
    pedagogical_score: float
    hallucination_rate: float
    cost: float
    pedagogical_breached: bool
    hallucination_breached: bool
    cost_breached: bool

    @property
    def has_breaches(self) -> bool:
        """Return ``True`` if any thresholds were exceeded."""

        return (
            self.pedagogical_breached
            or self.hallucination_breached
            or self.cost_breached
        )

    def breach_payload(self) -> Dict[str, float]:
        """Return metric values that breached thresholds."""

        data: Dict[str, float] = {}
        if self.pedagogical_breached:
            data["pedagogical_score"] = self.pedagogical_score
        if self.hallucination_breached:
            data["hallucination_rate"] = self.hallucination_rate
        if self.cost_breached:
            data["cost"] = self.cost
        return data


class AlertManager:
    """Evaluate metric thresholds and send webhooks on breaches."""

    def __init__(
        self,
        repository: MetricsRepository,
        thresholds_path: Path | None = None,
        webhook_url: str | None = None,
    ) -> None:
        self._repo = repository
        path = (
            thresholds_path
            if thresholds_path is not None
            else Path(__file__).resolve().parents[1] / "config" / "thresholds.yaml"
        )
        with open(path, "r", encoding="utf-8") as fh:
            self._thresholds = yaml.safe_load(fh)
        self._webhook_url = webhook_url or os.getenv("ALERT_WEBHOOK_URL")

    def evaluate_thresholds(self, workspace_id: str) -> AlertSummary:
        """Compare recent metrics against configured thresholds."""

        ped = self._repo.latest_value(workspace_id, "pedagogical_score") or 0.0
        halluc = self._repo.latest_value(workspace_id, "hallucination_rate") or 0.0
        cost = self._repo.latest_value(workspace_id, "cost") or 0.0

        ped_breach = ped < self._thresholds["pedagogical_score"]
        hall_breach = halluc > self._thresholds["max_hallucination_rate"]
        cost_breach = cost > self._thresholds["max_cost_per_lecture"]

        return AlertSummary(
            workspace_id=workspace_id,
            pedagogical_score=ped,
            hallucination_rate=halluc,
            cost=cost,
            pedagogical_breached=ped_breach,
            hallucination_breached=hall_breach,
            cost_breached=cost_breach,
        )

    def send_webhook(self, alert: AlertSummary) -> None:
        """POST ``alert`` details to the configured webhook if any breaches."""

        if not self._webhook_url or not alert.has_breaches:
            return

        payload: Dict[str, Any] = {
            "workspace_id": alert.workspace_id,
            "breaches": alert.breach_payload(),
        }
        httpx.post(self._webhook_url, json=payload, timeout=10.0)
