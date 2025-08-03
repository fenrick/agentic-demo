"""Application state model used by orchestration graphs.

This module re-exports the core :class:`State` model so that orchestration
components can import it from a dedicated subpackage without creating a hard
dependency on the broader core package structure.
"""

from __future__ import annotations

from core.state import State

__all__ = ["State"]
