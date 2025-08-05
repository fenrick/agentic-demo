"""Lightweight dense retriever using pure Python arrays."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .researcher_web import RawSearchResult


class DenseRetriever:
    """Perform simple dense similarity search over snippets."""

    _DIM = 64

    def __init__(self, documents: List["RawSearchResult"]) -> None:
        self._docs = documents
        self._vectors = [self._embed(d.snippet) for d in documents]

    @classmethod
    def _embed(cls, text: str) -> List[float]:
        arr = [0.0] * cls._DIM
        data = text.encode("utf-8")[: cls._DIM]
        for i, b in enumerate(data):
            arr[i] = float(b)
        return arr

    def search(self, query: str, k: int = 5) -> List["RawSearchResult"]:
        """Return top ``k`` documents similar to ``query``."""

        if not self._docs:
            return []
        qvec = self._embed(query)

        def dist(vec):
            return sum((a - b) ** 2 for a, b in zip(vec, qvec))

        order = sorted(range(len(self._vectors)), key=lambda i: dist(self._vectors[i]))[
            :k
        ]
        return [self._docs[i] for i in order]
