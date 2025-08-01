"""Utility helpers for the app."""

from __future__ import annotations

import pathlib
try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    yaml = None

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
    text = path.read_text()
    data = _safe_load(text)
    return data.get("content") or data["prompt"]


def _safe_load(text: str) -> dict:
    """Load YAML text with a minimal fallback parser."""
    if yaml is not None:
        return yaml.safe_load(text)

    lines = text.splitlines()
    if not lines:
        return {}
    key, _, rest = lines[0].partition(":")
    value = rest.strip()
    if value == "|":
        from textwrap import dedent
        value = dedent("\n".join(lines[1:])).lstrip()
    return {key.strip(): value}
