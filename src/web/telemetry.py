"""OpenTelemetry instruments for the web layer."""

from __future__ import annotations

from observability import meter

# Counters and histograms used across the API.
REQUEST_COUNTER = meter.create_counter(
    "requests_total", description="HTTP requests received"
)
SSE_CLIENTS = meter.create_up_down_counter(
    "sse_clients", description="Active SSE client connections"
)
EXPORT_DURATION = meter.create_histogram(
    "export_duration_ms", unit="ms", description="Export operation duration"
)

__all__ = ["REQUEST_COUNTER", "SSE_CLIENTS", "EXPORT_DURATION"]
