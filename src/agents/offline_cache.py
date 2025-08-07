"""Offline search result caching utilities."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from config import Settings


def _cache_dir() -> Path:
    """Return the directory used for storing cached results."""

    return Settings().data_dir / "cache"


if TYPE_CHECKING:  # pragma: no cover - imported for type hints only
    from .researcher_web import RawSearchResult


def _cache_file(query: str) -> Path:
    """Return filesystem path for ``query``'s cached results."""
    sanitized = re.sub(r"[^A-Za-z0-9_-]", "_", query)
    return _cache_dir() / f"{sanitized}.json"


def load_cached_results(query: str) -> Optional[List["RawSearchResult"]]:
    """Load cached search results for ``query`` if available."""
    from .researcher_web import RawSearchResult

    path = _cache_file(query)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return [RawSearchResult.model_validate(item) for item in data]


def save_cached_results(query: str, results: List["RawSearchResult"]) -> None:
    """Persist ``results`` for ``query`` to the cache directory."""
    cache_dir = _cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / _cache_file(query).name
    data = [result.model_dump() for result in results]
    path.write_text(json.dumps(data))
