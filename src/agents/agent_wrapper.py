"""Utility helpers for LLM interactions."""

from __future__ import annotations

from typing import Any, Dict, Optional

from agentic_demo import config


def get_llm_params(**overrides: Any) -> Dict[str, Any]:
    """Return default parameters for LangChain LLM calls.

    Reads the configured model name and merges any ``overrides`` provided,
    ensuring every request specifies the enforced model.
    """

    params: Dict[str, Any] = {"model": config.settings.model_name}
    params.update(overrides)
    return params


def init_chat_model(**overrides: Any) -> Optional[Any]:
    """Instantiate a chat model using a unified factory.

    The function inspects the configured model name (or an override) and
    returns an appropriate LangChain chat model instance.  Currently supports
    OpenAI and Perplexity Sonar models.  If the required dependency is not
    available, ``None`` is returned.

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

    try:
        if model_name.startswith("sonar"):
            from langchain_perplexity import ChatPerplexity  # type: ignore

            pplx_api_key = params.pop(
                "pplx_api_key", config.settings.perplexity_api_key
            )
            return ChatPerplexity(model=model_name, pplx_api_key=pplx_api_key, **params)

        from langchain_openai import ChatOpenAI  # type: ignore

        return ChatOpenAI(model=model_name, **params)
    except Exception:  # pragma: no cover - optional dependencies
        return None


__all__ = ["get_llm_params", "init_chat_model"]
