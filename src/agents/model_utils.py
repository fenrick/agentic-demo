"""Utilities for initializing Pydantic AI models."""

from __future__ import annotations

from typing import Any, Dict

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

import config

_MODEL_CACHE: Dict[str, OpenAIModel] = {}


def clear_model_cache() -> None:
    """Clear cached model instances."""

    _MODEL_CACHE.clear()


def init_model(**overrides: Any) -> OpenAIModel | None:
    """Instantiate or retrieve a cached Pydantic AI model."""

    settings = config.load_settings()
    model_id: str = overrides.pop("model", settings.model)
    provider_name, model_name = model_id.split(":", 1)

    if model_id in _MODEL_CACHE:
        return _MODEL_CACHE[model_id]

    if provider_name == "perplexity":
        pplx_api_key = overrides.pop("pplx_api_key", settings.perplexity_api_key)
        provider = OpenAIProvider(
            base_url="https://api.perplexity.ai", api_key=pplx_api_key
        )
    else:
        provider = OpenAIProvider()

    model = OpenAIModel(model_name, provider=provider)
    _MODEL_CACHE[model_id] = model
    return model


__all__ = ["init_model", "clear_model_cache"]
