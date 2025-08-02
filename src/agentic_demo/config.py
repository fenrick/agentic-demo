"""Environment configuration utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class EnvConfig:
    """Application environment settings."""

    openai_api_key: str
    perplexity_api_key: str
    model_name: str
    data_dir: str


def load_env(path: str | Path = ".env") -> EnvConfig:
    """Load environment settings from *path*.

    Args:
        path: Location of a ``.env`` file.

    Returns:
        Loaded :class:`EnvConfig` instance.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        KeyError: If a required key is missing.
    """

    raw = _parse_env(path)
    for key in _REQUIRED_KEYS:
        if key in os.environ:
            raw[key] = os.environ[key]
    missing = [key for key in _REQUIRED_KEYS if key not in raw]
    if missing:
        raise KeyError(f"Missing keys: {', '.join(missing)}")
    return EnvConfig(
        openai_api_key=raw["OPENAI_API_KEY"],
        perplexity_api_key=raw["PERPLEXITY_API_KEY"],
        model_name=raw["MODEL_NAME"],
        data_dir=raw["DATA_DIR"],
    )


_REQUIRED_KEYS = {
    "OPENAI_API_KEY",
    "PERPLEXITY_API_KEY",
    "MODEL_NAME",
    "DATA_DIR",
}


def _parse_env(path: str | Path) -> Dict[str, str]:
    """Parse key-value pairs from *path*.

    Args:
        path: Location of a ``.env`` file.

    Returns:
        Mapping of keys to values.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """

    data: Dict[str, str] = {}
    with open(path) as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip()
    return data
