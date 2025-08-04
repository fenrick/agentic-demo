"""Utilities for serialising :class:`~core.state.Outline` to Parquet."""

from __future__ import annotations

import io
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from core.state import Outline

from .parquet_schema import OUTLINE_SCHEMA


class ParquetSerializer:
    """Convert :class:`Outline` instances to and from Parquet blobs."""

    @staticmethod
    def serialize_outline(outline: Outline) -> bytes:
        """Serialise ``outline`` into a Parquet byte string using a fixed schema."""
        table = pa.Table.from_pylist([{"steps": outline.steps}], schema=OUTLINE_SCHEMA)
        sink = io.BytesIO()
        pq.write_table(table, sink)
        return sink.getvalue()

    @staticmethod
    def deserialize_outline(blob: bytes) -> Outline:
        """Deserialise ``blob`` back into an :class:`Outline` using the fixed schema."""
        source = io.BytesIO(blob)
        table = pq.read_table(source)
        table = table.cast(OUTLINE_SCHEMA)
        data: Any = table.to_pylist()[0]
        steps = data.get("steps", [])
        return Outline(steps=steps)
