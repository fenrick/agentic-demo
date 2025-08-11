"""Pipeline orchestration for researcher web search."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import List

import httpx

from core.state import State
from persistence import Citation, CitationRepo, get_db_session

from .copyright_filter import filter_allowlist
from .researcher_web import CitationDraft, rank_by_authority
from .researcher_web_runner import run_web_search


async def _lookup_licence(url: str) -> str:
    """Fetch licence information via HTTP HEAD."""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(url, timeout=5.0)
            return response.headers.get("License", "")
    except Exception:
        logging.exception("Failed to look up licence")
        return ""


async def researcher_pipeline(query: str, state: State) -> List[Citation]:
    """Execute the researcher pipeline for ``query``."""

    state.prompt = query
    try:
        drafts: List[CitationDraft] = await run_web_search(state)
    except Exception:
        logging.exception("Web search failed")
        return []

    ranked = rank_by_authority(drafts)
    kept, _ = filter_allowlist(ranked)
    citations: List[Citation] = []
    workspace_id = getattr(state, "workspace_id", "default")

    try:
        licence_results: List[str | BaseException] = await asyncio.gather(
            *(_lookup_licence(draft.url) for draft in kept),
            return_exceptions=True,
        )
    except Exception:
        logging.exception("Licence lookups failed")
        licence_results = ["unknown" for _ in kept]

    async with get_db_session() as conn:
        repo = CitationRepo(conn, workspace_id)
        for draft, licence in zip(kept, licence_results):
            licence_text = "unknown"
            if isinstance(licence, BaseException):
                logging.exception("Licence lookup failed for %s", draft.url)
            elif isinstance(licence, str) and licence:
                licence_text = licence

            citation = Citation(
                url=draft.url,
                title=draft.title,
                retrieved_at=datetime.utcnow(),
                licence=licence_text,
            )
            try:
                await repo.insert(citation)
            except Exception:
                logging.exception("Failed to insert citation for %s", draft.url)
                continue
            citations.append(citation)
    return citations
