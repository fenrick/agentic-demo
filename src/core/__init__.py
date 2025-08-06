"""Core utilities and base classes for agent components.

This module provides minimal infrastructure that can be reused across the
project.  The :class:`Agent` base class defines the interface for all agents
and offers a simple logger through :func:`get_logger`.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

__all__ = ["Agent", "AgentError", "get_logger"]


class AgentError(Exception):
    """Base exception for agent-related failures."""


class Agent(ABC):
    """Abstract base class for all agents.

    Parameters
    ----------
    name:
        Human-readable identifier used for logging and debugging.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = get_logger(name)

    @abstractmethod
    def act(self, message: str, /, **kwargs: Any) -> Any:
        """Execute the agent's core behaviour and return the result."""


def get_logger(name: str) -> logging.Logger:
    """Return a ``logging.Logger`` configured for ``name``."""

    return logging.getLogger(name)
