"""Utility helpers for LLM interactions."""

from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace
from typing import Any, Dict, Optional

from pydantic_ai.messages import (
    ModelRequest,
    PartDeltaEvent,
    TextPartDelta,
    UserPromptPart,
)
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

import config

# Cache of initialized chat models keyed by provider:model identifier.
_MODEL_CACHE: Dict[str, "PydanticAIChatModel"] = {}


class PydanticAIChatModel:
    """Minimal wrapper providing LangChain-like interfaces."""

    def __init__(self, model_name: str, provider: OpenAIProvider) -> None:
        self._model = OpenAIModel(model_name, provider=provider)

    def invoke(self, prompt: str) -> SimpleNamespace:
        """Synchronously request a completion."""

        async def _run() -> SimpleNamespace:
            request = ModelRequest(parts=[UserPromptPart(prompt)])
            resp = await self._model.request([request], None, ModelRequestParameters())
            text = "".join(
                part.content for part in resp.parts if hasattr(part, "content")
            )
            return SimpleNamespace(content=text, additional_kwargs=resp.vendor_details)

        return asyncio.run(_run())

    async def ainvoke(self, messages: list[Any]) -> SimpleNamespace:
        """Asynchronously request a completion."""

        request = ModelRequest(parts=list(messages))
        resp = await self._model.request([request], None, ModelRequestParameters())
        text = "".join(part.content for part in resp.parts if hasattr(part, "content"))
        return SimpleNamespace(content=text, additional_kwargs=resp.vendor_details)

    async def astream(self, messages: list[Any]):
        """Yield streamed text deltas from the model."""

        request = ModelRequest(parts=list(messages))
        async with self._model.request_stream(
            [request], None, ModelRequestParameters()
        ) as stream:
            async for event in stream:
                if isinstance(event, PartDeltaEvent) and isinstance(
                    event.delta, TextPartDelta
                ):
                    yield event.delta.content_delta


def clear_model_cache() -> None:
    """Clear cached chat model instances."""

    _MODEL_CACHE.clear()


def init_chat_model(**overrides: Any) -> Optional[PydanticAIChatModel]:
    """Instantiate or retrieve a cached Pydantic AI model."""

    settings = config.load_settings()
    model_id: str = overrides.pop("model", settings.model)
    provider_name, model_name = model_id.split(":", 1)

    if model_id in _MODEL_CACHE:
        return _MODEL_CACHE[model_id]

    try:
        if provider_name == "perplexity":
            pplx_api_key = overrides.pop("pplx_api_key", settings.perplexity_api_key)
            provider = OpenAIProvider(
                base_url="https://api.perplexity.ai", api_key=pplx_api_key
            )
        else:
            provider = OpenAIProvider()

        model = PydanticAIChatModel(model_name, provider)
        _MODEL_CACHE[model_id] = model
        return model
    except Exception:  # pragma: no cover - optional dependencies
        logging.exception("Failed to initialize chat model")
        return None


__all__ = ["init_chat_model", "clear_model_cache"]
