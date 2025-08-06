"""Concrete agent implementations built on :mod:`core` utilities."""

from __future__ import annotations

from core import Agent

__all__ = ["EchoAgent", "ReverseAgent"]


class EchoAgent(Agent):
    """Return the provided message unchanged."""

    def act(self, message: str, /, **kwargs: object) -> str:
        self.logger.debug("echoing %s", message)
        return message


class ReverseAgent(Agent):
    """Return the reversed representation of the provided message."""

    def act(self, message: str, /, **kwargs: object) -> str:
        self.logger.debug("reversing %s", message)
        return message[::-1]
