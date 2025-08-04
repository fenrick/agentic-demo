"""Utility helpers for LLM interactions."""

from __future__ import annotations

from typing import Any, Dict

from agentic_demo import config


def get_llm_params(**overrides: Any) -> Dict[str, Any]:
    """Return default parameters for OpenAI calls.

    Reads the configured model name and merges any ``overrides`` provided,
    ensuring every request specifies the enforced model.
    """

    params: Dict[str, Any] = {"model": config.settings.model_name}
    params.update(overrides)
    return params


__all__ = ["get_llm_params"]
