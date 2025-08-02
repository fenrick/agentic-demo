"""Async retry utilities."""

from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


def retry_async(
    max_retries: int = 3,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Retry an async function up to ``max_retries`` times.

    Args:
        max_retries: Maximum number of attempts before propagating the exception.

    Returns:
        Decorated function with retry behavior.

    Side Effects:
        Retries the wrapped function upon exception.

    Exceptions:
        Re-raises the last exception after exhausting retries.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            attempts = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception:  # pragma: no cover - exercised via tests
                    attempts += 1
                    if attempts >= max_retries:
                        raise

        return wrapper

    return decorator
