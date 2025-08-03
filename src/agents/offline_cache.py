"""Offline search result caching utilities."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

# Directory for cached search results
CACHE_DIR = Path("workspace/cache")

if TYPE_CHECKING:  # pragma: no cover - imported for type hints only
    from .researcher_web import RawSearchResult


def _cache_file(query: str) -> Path:
    """Return filesystem path for ``query``'s cached results."""
    sanitized = re.sub(r"[^A-Za-z0-9_-]", "_", query)
    return CACHE_DIR / f"{sanitized}.json"


def load_cached_results(query: str) -> Optional[List["RawSearchResult"]]:
    """Load cached search results for ``query`` if available."""
    from .researcher_web import RawSearchResult

    path = _cache_file(query)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return [RawSearchResult(**item) for item in data]


def save_cached_results(query: str, results: List["RawSearchResult"]) -> None:
    """Persist ``results`` for ``query`` to the cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_file(query)
    data = [asdict(result) for result in results]
    path.write_text(json.dumps(data))
