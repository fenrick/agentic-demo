from typing import Any, Dict


class ChatCompletion:
    """Simplistic stub for openai.ChatCompletion.

    Returns a placeholder response when the real ``openai`` package is
    unavailable.
    """

    @staticmethod
    def create(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"choices": [{"message": {"content": "stub response"}}]}


class Responses:
    """Placeholder for the ``openai.Responses`` API."""

    @staticmethod
    def create(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Return a generic response mimicking the real API."""
        return {"choices": [{"message": {"content": "stub response"}}]}
