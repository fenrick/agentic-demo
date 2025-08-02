"""Tests for presence of new packages.

These tests ensure that the top-level architectural packages exist and are
importable. The packages currently act as placeholders for future
implementation.
"""

from importlib import import_module

import pytest


@pytest.mark.parametrize(
    "package_name",
    ["core", "agents", "persistence", "web", "export"],
)
def test_package_is_importable(package_name: str) -> None:
    """Verify that the placeholder package can be imported.

    Parameters
    ----------
    package_name:
        The dotted path of the package to import.
    """
    module = import_module(package_name)
    assert module.__spec__ is not None
