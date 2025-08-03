"""Dataclass for action log records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ActionLog:
    """Record of an agent invocation."""

    workspace_id: str
    agent_name: str
    input_hash: str
    output_hash: str
    tokens: int
    cost: float
    timestamp: datetime
