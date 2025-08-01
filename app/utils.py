"""Utility helpers for the app."""

from __future__ import annotations

import pathlib
import yaml

PROMPTS_PATH = pathlib.Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template by name.

    Parameters
    ----------
    name : str
        Name of the YAML file without extension.

    Returns
    -------
    str
        The template string.

    Raises
    ------
    FileNotFoundError
        If the prompt file does not exist.
    """
    path = PROMPTS_PATH / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text())
    return data["content"]
