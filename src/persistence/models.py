"""Persistence data models."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, HttpUrl


class Citation(BaseModel):
    """Stored reference to an external source."""

    url: HttpUrl
    title: str
    retrieved_at: datetime
    licence: str
