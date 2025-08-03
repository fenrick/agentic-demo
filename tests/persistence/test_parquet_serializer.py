"""Tests for :mod:`persistence.parquet_serializer`."""

from __future__ import annotations

from persistence.parquet_serializer import ParquetSerializer
from core.state import Outline


def test_round_trip_simple_outline() -> None:
    outline = Outline(steps=["intro", "body", "conclusion"])
    blob = ParquetSerializer.serialize_outline(outline)
    restored = ParquetSerializer.deserialize_outline(blob)
    assert restored == outline


def test_round_trip_empty_outline() -> None:
    outline = Outline(steps=[])
    blob = ParquetSerializer.serialize_outline(outline)
    restored = ParquetSerializer.deserialize_outline(blob)
    assert restored == outline


def test_round_trip_large_outline() -> None:
    steps = [f"step-{i}" for i in range(1000)]
    outline = Outline(steps=steps)
    blob = ParquetSerializer.serialize_outline(outline)
    restored = ParquetSerializer.deserialize_outline(blob)
    assert restored == outline
