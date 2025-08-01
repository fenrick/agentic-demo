"""Agents used in the demo."""

from __future__ import annotations

from typing import Any, Dict
import logging
from datetime import datetime, timezone

from langsmith import run_helpers

try:  # attempt to use the real client if available
    import openai as _openai
except ModuleNotFoundError:  # pragma: no cover - fallback for testing
    import openai_stub as _openai  # type: ignore

openai: Any = _openai

FALLBACK_MESSAGE = "OpenAI API unavailable"

logger = logging.getLogger(__name__)


class ChatAgent:
    """Simple wrapper around the OpenAI chat completion API.

    Parameters
    ----------
    model:
        Name of the chat model to invoke.
    fallback:
        Message returned when the OpenAI client is unavailable or errors occur.
    """

    def __init__(
        self, model: str = "gpt-3.5-turbo", *, fallback: str | None = None
    ) -> None:
        self.model = model
        self.fallback = fallback or FALLBACK_MESSAGE

    def __call__(self, messages: list[Dict[str, str]]) -> str:
        """Call the chat completion API with the provided messages.

        If the OpenAI dependency is missing or raises an error, ``fallback`` is
        returned instead.
        """
        try:
            create = openai.ChatCompletion.create
        except AttributeError:
            return self.fallback

        try:
            response = create(model=self.model, messages=messages)
        except Exception:
            return self.fallback

        return response["choices"][0]["message"]["content"].strip()


def _call_agent(prompt: str, agent: ChatAgent | None) -> str:
    """Send ``prompt`` to ``agent`` and return the response text.

    Parameters
    ----------
    prompt:
        Text to be passed to the chat model.
    agent:
        Instance of :class:`ChatAgent` to use. If ``None`` a default
        ``ChatAgent`` is created.

    Returns
    -------
    str
        Response from the chat agent. If the underlying agent encounters an
        error, its fallback message is returned.
    """

    use_agent = agent or ChatAgent()
    messages = [{"role": "user", "content": prompt}]
    return use_agent(messages)


def _log_metrics(text: str, loop: int) -> None:
    """Record token, loop and citation statistics with LangSmith."""
    # TODO: replace naive token counting with tiktoken when available
    token_count = len(text.split())
    citation_tokens = text.count("[")
    coverage = citation_tokens / token_count if token_count else 0
    run = run_helpers.get_current_run_tree()
    if run:
        run.add_event(
            {
                "name": "metrics",
                "time": datetime.now(timezone.utc).isoformat(),
                "kwargs": {
                    "token_count": token_count,
                    "loop_count": loop,
                    "citation_coverage": coverage,
                },
            }
        )
    logger.info(
        "tokens=%s loop=%s citation=%.2f",
        token_count,
        loop,
        coverage,
    )


@run_helpers.traceable
def plan(topic: str, *, agent: ChatAgent | None = None, loop: int = 0) -> str:
    """Generate a short plan for the given topic."""
    text = _call_agent(f"Create an outline for {topic}.", agent)
    _log_metrics(text, loop)
    return text


@run_helpers.traceable
def research(
    outline: str,
    *,
    agent: ChatAgent | None = None,
    loop: int = 0,
) -> str:
    """Return research notes for the outline."""
    text = _call_agent(f"Provide background facts about: {outline}", agent)
    _log_metrics(text, loop)
    return text


@run_helpers.traceable
def draft(
    notes: str,
    *,
    agent: ChatAgent | None = None,
    loop: int = 0,
) -> str:
    """Draft content from notes."""
    text = _call_agent(f"Write a short passage using: {notes}", agent)
    _log_metrics(text, loop)
    return text


@run_helpers.traceable
def review(
    text: str,
    *,
    agent: ChatAgent | None = None,
    loop: int = 0,
) -> str:
    """Review and polish the text."""
    result = _call_agent(f"Improve the following text for clarity:\n{text}", agent)
    _log_metrics(result, loop)
    return result
