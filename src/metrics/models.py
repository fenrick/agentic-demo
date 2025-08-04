"""Data models for metrics collection and querying."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MetricRecord:
    """Single metric data point."""

    name: str
    value: float
    timestamp: datetime


@dataclass
class TimeRange:
    """Inclusive time span for metric queries."""

    start: datetime
    end: datetime
