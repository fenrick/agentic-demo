"""Data models for metrics collection and querying."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MetricRecord:
    """Single metric data point.

    Attributes
    ----------
    workspace_id:
        Identifier for the workspace the metric belongs to.
    name:
        Metric identifier such as ``tokens`` or ``cost``.
    value:
        Numeric value for the metric.
    timestamp:
        When the metric was recorded.
    """

    workspace_id: str
    name: str
    value: float
    timestamp: datetime


@dataclass
class TimeRange:
    """Inclusive time span for metric queries."""

    start: datetime
    end: datetime
