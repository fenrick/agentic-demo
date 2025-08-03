"""Async web researcher utilities."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable, List
from urllib.parse import urlparse
import urllib.request


@dataclass(slots=True)
class CitationResult:
    """Result of fetching a URL.

    Attributes:
        url: The original URL fetched.
        content: Text content retrieved from the URL.
    """

    url: str
    content: str


async def _fetch(url: str) -> CitationResult:
    """Fetch the contents of ``url`` asynchronously."""

    def blocking_fetch() -> str:
        with urllib.request.urlopen(url) as response:  # nosec B310
            return response.read().decode("utf-8")  # pragma: no cover - network

    content = await asyncio.to_thread(blocking_fetch)
    return CitationResult(url=url, content=content)


def _canonical(url: str) -> str:
    """Return a canonical form of ``url`` for deduplication.

    The canonical form strips scheme, query, and fragment components,
    lower-cases the hostname and path, and removes any leading ``www``.
    """

    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.lower().rstrip("/")
    return f"{netloc}{path}"


async def researcher_web(
    urls: Iterable[str],
    fetch: Callable[[str], Awaitable[CitationResult]] | None = None,
) -> List[CitationResult]:
    """Fetch multiple URLs concurrently and deduplicate results.

    Args:
        urls: Iterable of URLs to fetch.
        fetch: Optional coroutine to fetch a single URL. Defaults to an internal
            implementation using :func:`asyncio.to_thread` and ``urllib``.

    Returns:
        Deduplicated list of :class:`CitationResult` objects preserving input order.
        Only the first result for each *similar* URL is retained.

    Exceptions are suppressed; failed fetches are omitted from the results.
    """

    fetch = fetch or _fetch
    tasks = [fetch(url) for url in urls]
    responses: List[CitationResult | BaseException] = await asyncio.gather(
        *tasks, return_exceptions=True
    )
    deduped: dict[str, CitationResult] = {}
    for result in responses:
        if isinstance(result, BaseException):
            continue
        key = _canonical(result.url)
        if key not in deduped:
            deduped[key] = result
    return list(deduped.values())
