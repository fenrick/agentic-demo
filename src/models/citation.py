"""Dataclass for citation records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Citation:
    """Stored reference to an external source."""

    workspace_id: str
    url: str
    title: str
    retrieved_at: datetime
    licence: str
