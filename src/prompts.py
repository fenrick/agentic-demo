"""Utility for loading LLM prompt templates from configuration."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict


@lru_cache()
def load_prompts() -> Dict[str, str]:
    """Load prompt texts from the adjacent JSON file once.

    Returns:
        Mapping of prompt names to their text templates.
    """

    config_path = Path(__file__).with_name("prompts.json")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_prompt(name: str) -> str:
    """Retrieve a prompt template by name.

    Args:
        name: Key of the desired prompt in the configuration.

    Returns:
        The prompt text associated with ``name``.

    Raises:
        KeyError: If ``name`` is not present in the configuration.
    """

    prompts = load_prompts()
    if name not in prompts:
        raise KeyError(f"unknown prompt '{name}'")
    return prompts[name]


__all__ = ["get_prompt", "load_prompts"]
