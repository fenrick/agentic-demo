"""Persistence data models."""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, HttpUrl


class Citation(BaseModel):
    """Stored reference to an external source."""

    url: HttpUrl
    title: str
    retrieved_at: datetime
    licence: str


class CachedSearchResult(BaseModel):
    """Cached search result snippet stored in the retrieval cache."""

    url: HttpUrl
    snippet: str
    title: str


class RetrievalCache(BaseModel):
    """Record of cached search results for a query."""

    query: str
    results: List[CachedSearchResult]
    hit_count: int
    created_at: datetime
