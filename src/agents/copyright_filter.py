"""Allowlist filtering for citation drafts."""

from __future__ import annotations

from typing import List
from urllib.parse import urlparse

from config import Settings

from .researcher_web import CitationDraft


def filter_allowlist(
    results: List[CitationDraft],
) -> tuple[List[CitationDraft], List[CitationDraft]]:
    """Split drafts into kept and dropped based on an allowlist."""

    settings = Settings()
    patterns = [p.lower() for p in settings.allowlist_domains]
    kept: List[CitationDraft] = []
    dropped: List[CitationDraft] = []
    for draft in results:
        domain = urlparse(draft.url).netloc.lower()
        if any(pattern in domain for pattern in patterns):
            kept.append(draft)
        else:
            dropped.append(draft)
    return kept, dropped
