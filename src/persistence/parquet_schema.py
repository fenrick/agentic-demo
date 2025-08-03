"""Shared Arrow schema definitions for Parquet serialisation."""

from __future__ import annotations

import pyarrow as pa

# Schema for the ``Outline`` model stored as Parquet.
# The outline currently stores a sequence of textual steps.
OUTLINE_SCHEMA = pa.schema(
    [
        ("steps", pa.list_(pa.string())),
    ]
)
