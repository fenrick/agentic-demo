"""Utility helpers for LLM interactions."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import config

# Cache of initialized chat models keyed by model name.
_MODEL_CACHE: Dict[str, Any] = {}


def clear_model_cache() -> None:
    """Clear cached chat model instances.

    Primarily intended for use in unit tests to ensure a clean slate between
    test cases.
    """

    _MODEL_CACHE.clear()


def get_llm_params(**overrides: Any) -> Dict[str, Any]:
    """Return default parameters for LangChain LLM calls.

    Reads the configured model name and merges any ``overrides`` provided,
    ensuring every request specifies the enforced model.
    """

    params: Dict[str, Any] = {"model": config.settings.model_name}
    params.update(overrides)
    return params


def init_chat_model(**overrides: Any) -> Optional[Any]:
    """Instantiate or retrieve a cached chat model instance.

    The function inspects the configured model name (or an override) and
    returns an appropriate LangChain chat model instance. Instances are cached
    by model name to avoid repeated construction. If the required dependency is
    not available, ``None`` is returned.

    Parameters
    ----------
    **overrides:
        Optional keyword arguments merged with the default LLM parameters.

    Returns
    -------
    Optional[Any]
        The instantiated chat model or ``None`` if construction failed.
    """

    params = get_llm_params(**overrides)
    model_name = params.pop("model", "")

    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    try:
        if model_name.startswith("sonar"):
            from langchain_perplexity import ChatPerplexity  # type: ignore

            pplx_api_key = params.pop(
                "pplx_api_key", config.settings.perplexity_api_key
            )
            model = ChatPerplexity(
                model=model_name, pplx_api_key=pplx_api_key, **params
            )
        else:
            from langchain_openai import ChatOpenAI  # type: ignore

            model = ChatOpenAI(model=model_name, **params)

        _MODEL_CACHE[model_name] = model
        return model
    except Exception:  # pragma: no cover - optional dependencies
        logging.exception("Failed to initialize chat model")
        return None


__all__ = ["get_llm_params", "init_chat_model", "clear_model_cache"]
