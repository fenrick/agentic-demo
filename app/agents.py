"""Agents used in the demo."""

from __future__ import annotations

import openai
from typing import Dict, Any


class ChatAgent:
    """Simple wrapper around the OpenAI chat completion API."""

    def __init__(self, model: str = "gpt-3.5-turbo") -> None:
        self.model = model

    def __call__(self, messages: list[Dict[str, str]]) -> str:
        """Call the chat completion API with the provided messages."""
        response = openai.ChatCompletion.create(model=self.model, messages=messages)
        return response["choices"][0]["message"]["content"].strip()


def _call_agent(prompt: str, agent: ChatAgent | None) -> str:
    use_agent = agent or ChatAgent()
    messages = [{"role": "user", "content": prompt}]
    return use_agent(messages)


def plan(topic: str, *, agent: ChatAgent | None = None) -> str:
    """Generate a short plan for the given topic."""
    return _call_agent(f"Create an outline for {topic}.", agent)


def research(outline: str, *, agent: ChatAgent | None = None) -> str:
    """Return research notes for the outline."""
    return _call_agent(f"Provide background facts about: {outline}", agent)


def draft(notes: str, *, agent: ChatAgent | None = None) -> str:
    """Draft content from notes."""
    return _call_agent(f"Write a short passage using: {notes}", agent)


def review(text: str, *, agent: ChatAgent | None = None) -> str:
    """Review and polish the text."""
    return _call_agent(f"Improve the following text for clarity:\n{text}", agent)
