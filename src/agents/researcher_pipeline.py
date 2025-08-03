"""Pipeline orchestration for researcher web search."""

from __future__ import annotations

from datetime import datetime
from typing import List

import httpx

from core.state import State
from persistence import Citation, CitationRepo, get_db_session

from .copyright_filter import filter_allowlist
from .researcher_web import CitationDraft, rank_by_authority
from .researcher_web_runner import run_web_search


def _lookup_licence(url: str) -> str:
    """Fetch licence information via HTTP HEAD."""

    try:
        response = httpx.head(url, timeout=5.0)
        return response.headers.get("License", "")
    except Exception:
        return ""


async def researcher_pipeline(query: str, state: State) -> List[Citation]:
    """Execute the researcher pipeline for ``query``."""

    state.prompt = query
    drafts: List[CitationDraft] = run_web_search(state)
    ranked = rank_by_authority(drafts)
    kept, _ = filter_allowlist(ranked)
    citations: List[Citation] = []
    workspace_id = getattr(state, "workspace_id", "default")
    async with get_db_session() as conn:
        repo = CitationRepo(conn, workspace_id)
        for draft in kept:
            citation = Citation(
                url=draft.url,
                title=draft.title,
                retrieved_at=datetime.utcnow(),
                licence=_lookup_licence(draft.url) or "unknown",
            )
            await repo.insert(citation)
            citations.append(citation)
    return citations
