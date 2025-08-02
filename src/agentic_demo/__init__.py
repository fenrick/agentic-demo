"""Top-level package for agentic-demo.

Provides foundational modules for demonstration purposes.
"""

from typing import List

from .config import EnvConfig, load_env

__all__: List[str] = ["EnvConfig", "load_env"]
