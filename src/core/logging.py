"""Centralized Loguru configuration for structured logging.

This module sets up Loguru to emit JSON-formatted logs and exposes a helper
for binding job and user identifiers. Modules should import ``get_logger``
and call it with any relevant IDs to obtain a context-aware logger instance.
"""

from __future__ import annotations

import sys
from typing import Optional

from loguru import logger as _logger


# Configure a single JSON sink for all application logs.
_logger.remove()
_logger.add(sys.stdout, serialize=True)


def get_logger(job_id: Optional[str] = None, user_id: Optional[str] = None):
    """Return a Loguru logger bound with job and user identifiers.

    Args:
        job_id: Identifier for the current job or workspace.
        user_id: Identifier for the acting user.

    Returns:
        ``loguru.Logger`` instance with the provided identifiers bound so
        they appear in every log record.
    """

    return _logger.bind(job_id=job_id, user_id=user_id)


# Export the base logger for modules that don't require additional context.
logger = _logger
