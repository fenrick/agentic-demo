"""Utilities for serialising :class:`~core.state.Outline` to Parquet."""

from __future__ import annotations

import io
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from core.state import Outline


class ParquetSerializer:
    """Convert :class:`Outline` instances to and from Parquet blobs."""

    @staticmethod
    def dumps(outline: Outline) -> bytes:
        """Serialise ``outline`` into a Parquet byte string."""
        table = pa.Table.from_pylist([{"steps": outline.steps}])
        sink = io.BytesIO()
        pq.write_table(table, sink)
        return sink.getvalue()

    @staticmethod
    def loads(blob: bytes) -> Outline:
        """Deserialise ``blob`` back into an :class:`Outline`."""
        source = io.BytesIO(blob)
        table = pq.read_table(source)
        data: Any = table.to_pylist()[0]
        steps = data.get("steps", [])
        return Outline(steps=steps)
