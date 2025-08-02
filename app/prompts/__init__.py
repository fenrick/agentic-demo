"""Prompt loading utilities."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_BASE = Path(__file__).resolve().parent

# TODO: support async loading if prompts move to remote storage.


@lru_cache
def get_prompt(name: str) -> str:
    """Return the text of a prompt.

    Parameters
    ----------
    name:
        Stem of the prompt file located under ``app/prompts``.

    Returns
    -------
    str
        Contents of the prompt file.

    Raises
    ------
    FileNotFoundError
        If the prompt file does not exist.
    """
    path = _BASE / f"{name}.txt"
    return path.read_text(encoding="utf-8")
