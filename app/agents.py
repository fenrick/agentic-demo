"""Agents used in the demo."""

from __future__ import annotations

import logging
from typing import Any, Dict
from datetime import datetime, timezone

from . import utils, perplexity
from langsmith import run_helpers

try:  # attempt to use the real client if available
    import openai as _openai
except ModuleNotFoundError:  # pragma: no cover - fallback for testing
    import openai_stub as _openai  # type: ignore

try:  # optional token counter dependency
    import tiktoken as _tiktoken  # type: ignore

    tokenizer: Any | None = _tiktoken
except ModuleNotFoundError:  # pragma: no cover - fallback when missing
    tokenizer = None

openai: Any = _openai

FALLBACK_MESSAGE = "OpenAI API unavailable"

logger = logging.getLogger(__name__)


class ChatAgent:
    """Simple wrapper around the ``openai.Responses`` API.

    Parameters
    ----------
    model:
        Name of the chat model to invoke.
    fallback:
        Message returned when the OpenAI client is unavailable or errors occur.
    """

    def __init__(
        self,
        model: str = "o4-mini",
        *,
        fallback: str | None = None,
    ) -> None:
        self.model = model
        self.fallback = fallback or FALLBACK_MESSAGE

    def __call__(self, messages: list[Dict[str, str]]) -> str:
        """Call the chosen OpenAI API with the provided messages.

        Falls back to ``fallback`` if the client or endpoint is unavailable.
        """
        try:
            create = openai.Responses.create
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
    system_prompt = utils.load_prompt("system")
    user_template = utils.load_prompt("user")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_template.format(input=prompt)},
    ]
    return use_agent(messages)


def _token_count(text: str) -> int:
    """Return the number of tokens in ``text``.

    Uses ``tiktoken`` when available and falls back to a simple word count.

    Parameters
    ----------
    text:
        Text to count tokens for.

    Returns
    -------
    int
        Calculated token count.
    """

    if tokenizer is None:
        return len(text.split())
    try:
        enc = tokenizer.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:  # pragma: no cover - tiktoken internal error
        return len(text.split())


def _log_metrics(text: str, loop: int) -> None:
    """Record token, loop and citation statistics with LangSmith."""
    token_count = _token_count(text)
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
    prompt = utils.load_prompt("plan").format(topic=topic)
    text = _call_agent(prompt, agent)
    _log_metrics(text, loop)
    return text


@run_helpers.traceable
def research(
    outline: str,
    *,
    agent: ChatAgent | None = None,
    loop: int = 0,
) -> str:
    """Return research notes for the outline.

    The function enriches the prompt with search results from Perplexity to
    provide the chat agent with up-to-date facts.
    """

    search_results = perplexity.search(outline)
    prompt = utils.load_prompt("research").format(
        outline=outline,
        search_results=search_results,
    )
    text = _call_agent(prompt, agent)
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
    prompt = utils.load_prompt("draft").format(notes=notes)
    text = _call_agent(prompt, agent)
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
    prompt = utils.load_prompt("review").format(text=text)
    result = _call_agent(prompt, agent)
    _log_metrics(result, loop)
    return result


class PedagogyCritic:
    """Placeholder agent that will critique generated lessons."""

    def __call__(self, text: str) -> str:
        """Return pedagogical feedback for ``text``.

        Parameters
        ----------
        text:
            Lesson content to evaluate.

        Returns
        -------
        str
            TODO: provide structured pedagogical critique.

        Raises
        ------
        NotImplementedError
            This placeholder has no behaviour yet.
        """

        # TODO: implement pedagogy critique logic using ChatAgent.
        # TODO: update ``app/graph.py`` to include this agent in the LangGraph flow.
        raise NotImplementedError("PedagogyCritic is not yet implemented")


class QAReviewer:
    """Placeholder agent that will perform quality assurance review."""

    def __call__(self, text: str) -> str:
        """Return QA notes for ``text``.

        Parameters
        ----------
        text:
            Draft content to review.

        Returns
        -------
        str
            TODO: return quality assurance findings.

        Raises
        ------
        NotImplementedError
            This placeholder has no behaviour yet.
        """

        # TODO: implement QA review logic using ChatAgent.
        # TODO: update ``app/graph.py`` to include this agent in the LangGraph flow.
        raise NotImplementedError("QAReviewer is not yet implemented")
