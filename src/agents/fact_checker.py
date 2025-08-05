"""Fact-checking agent detecting hallucinations and unsupported claims."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import List

import httpx

from config import Settings
from core.state import State
from models import ClaimFlag, FactCheckReport, SentenceProbability

_DEF_LOW_CONF_WORDS = ["maybe", "probably", "i think", "uncertain"]


def assess_hallucination_probabilities(text: str) -> List[SentenceProbability]:
    """Assign confidence scores to sentences and return low-confidence ones."""

    sentences = [s.strip() for s in re.split(r"[.!?]\s*", text) if s.strip()]
    results: List[SentenceProbability] = []
    for idx, sentence in enumerate(sentences, start=1):
        lowered = sentence.lower()
        probability = 0.9
        if any(word in lowered for word in _DEF_LOW_CONF_WORDS):
            probability = 0.4
        if probability < 0.6:
            results.append(
                SentenceProbability(
                    line_number=idx, sentence=sentence, probability=probability
                )
            )
    return results


_UNSUPPORTED_PATTERN = re.compile(
    r"(studies show|experts say|research indicates)", re.IGNORECASE
)
_CITATION_PATTERN = re.compile(r"\[[0-9]+\]|\(.*?\d{4}.*?\)")


def scan_unsupported_claims(text: str) -> List[ClaimFlag]:
    """Detect claim phrases lacking accompanying citations."""

    flags: List[ClaimFlag] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if _UNSUPPORTED_PATTERN.search(line) and not _CITATION_PATTERN.search(line):
            flags.append(ClaimFlag(line_number=idx, snippet=line.strip()))
    return flags


def compile_fact_check_report(
    hallucinations: List[SentenceProbability], flags: List[ClaimFlag]
) -> FactCheckReport:
    """Aggregate hallucination and claim checks into a report."""

    return FactCheckReport(
        hallucinations=hallucinations,
        unsupported_claims=flags,
        hallucination_count=len(hallucinations),
        unsupported_claims_count=len(flags),
    )


async def run_fact_checker(state: State) -> FactCheckReport:
    """Orchestrate fact-checking on the state's outline steps.

    The outline represents content as an ordered list of textual steps.
    This function joins the steps into a single string for analysis.
    """

    outline = getattr(state, "outline", None)
    if outline is None or not getattr(outline, "steps", None):
        raise ValueError("state.outline.steps is required for fact checking")
    text = "\n".join(outline.steps)
    hallucinations = assess_hallucination_probabilities(text)
    flags = scan_unsupported_claims(text)
    return compile_fact_check_report(hallucinations, flags)


__all__ = [
    "assess_hallucination_probabilities",
    "scan_unsupported_claims",
    "compile_fact_check_report",
    "run_fact_checker",
    "verify_sources",
    "SourceVerification",
]


@dataclass(slots=True)
class SourceVerification:
    """Result of verifying an external information source."""

    url: str
    status: str
    licence: str | None = None


async def verify_sources(urls: List[str]) -> List[SourceVerification]:
    """Validate external URLs and capture licence metadata.

    When the application runs in offline mode, network calls are skipped and
    each source is marked as ``unchecked``.
    """

    settings = Settings()
    if settings.offline_mode:
        return [SourceVerification(url=url, status="unchecked") for url in urls]

    async def _verify(client: httpx.AsyncClient, url: str) -> SourceVerification:
        try:
            response = await client.head(url, timeout=5.0)
            status = "ok" if response.status_code < 400 else "error"
            licence = response.headers.get("License")
        except Exception:
            logging.exception("Source verification failed")
            status = "error"
            licence = None
        return SourceVerification(url=url, status=status, licence=licence)

    async with httpx.AsyncClient() as client:
        tasks = [_verify(client, url) for url in urls]
        return await asyncio.gather(*tasks)
