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
