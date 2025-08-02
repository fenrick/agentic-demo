"""Tests for the :mod:`agentic_demo.greeting` module."""

import pytest

from agentic_demo.greeting import Greeter


@pytest.fixture
def greeter() -> Greeter:
    """Provide a default :class:`Greeter` instance."""
    return Greeter()


def test_greet_with_default_prefix(greeter: Greeter) -> None:
    """``Greeter.greet`` uses the default prefix."""
    assert greeter.greet("Alice") == "Hello, Alice!"


def test_greet_with_custom_prefix() -> None:
    """``Greeter.greet`` respects a custom prefix."""
    assert Greeter(prefix="Hi").greet("Bob") == "Hi, Bob!"


def test_greet_empty_name_raises(greeter: Greeter) -> None:
    """``Greeter.greet`` validates input."""
    with pytest.raises(ValueError):
        greeter.greet("")
