"""Schemas for Server-Sent Events."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class SseEvent(BaseModel):
    """Structure of an SSE message."""

    type: str
    payload: dict
    timestamp: datetime
