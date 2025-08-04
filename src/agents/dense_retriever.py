"""Lightweight dense retriever using FAISS with a NumPy fallback."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

import numpy as np

try:  # pragma: no cover - optional dependency
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = None

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .researcher_web import RawSearchResult


class DenseRetriever:
    """Perform simple dense similarity search over snippets."""

    _DIM = 64

    def __init__(self, documents: List["RawSearchResult"]) -> None:
        self._docs = documents
        vectors = self._embed_batch([d.snippet for d in documents])
        if faiss is not None and vectors.size > 0:
            self._index = faiss.IndexFlatL2(self._DIM)
            self._index.add(vectors)
            self._vectors = None
        else:
            self._index = None
            self._vectors = vectors

    @classmethod
    def _embed(cls, text: str) -> np.ndarray:
        arr = np.zeros(cls._DIM, dtype="float32")
        data = text.encode("utf-8")[: cls._DIM]
        for i, b in enumerate(data):
            arr[i] = float(b)
        return arr

    @classmethod
    def _embed_batch(cls, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, cls._DIM), dtype="float32")
        return np.vstack([cls._embed(t) for t in texts])

    def search(self, query: str, k: int = 5) -> List["RawSearchResult"]:
        """Return top ``k`` documents similar to ``query``."""

        if not self._docs:
            return []
        vector = self._embed(query).reshape(1, -1)
        if self._index is not None:
            _, indices = self._index.search(vector, k)
            return [self._docs[i] for i in indices[0] if i < len(self._docs)]
        distances = ((self._vectors - vector) ** 2).sum(axis=1)
        order = np.argsort(distances)[:k]
        return [self._docs[i] for i in order]
