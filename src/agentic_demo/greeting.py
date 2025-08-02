"""Greeting utilities.

Defines the :class:`Greeter` for producing friendly salutations.

TODO: Support localization for multiple languages.
"""

from dataclasses import dataclass


@dataclass
class Greeter:
    """Produces greeting messages.

    Attributes:
        prefix: Greeting prefix to use in messages.
    """

    prefix: str = "Hello"

    def greet(self, name: str) -> str:
        """Return a greeting for *name*.

        Args:
            name: Person to greet.

        Returns:
            Fully formatted greeting string.

        Raises:
            ValueError: If ``name`` is empty.
        """

        if not name:
            raise ValueError("name must not be empty")
        return f"{self.prefix}, {name}!"
