class ValidationError(Exception):
    """Minimal stub of ``pydantic.ValidationError`` used in tests."""


class BaseModel:
    """Very small stand-in for :class:`pydantic.BaseModel`.

    It simply assigns provided keyword arguments to attributes without any
    validation.  This is sufficient for the unit tests which only need to store
    and retrieve data objects.
    """

    def __init__(self, **data):
        for key, value in data.items():
            setattr(self, key, value)

    def model_dump(self) -> dict:
        """Return a JSON-serializable representation of the model."""

        return self.__dict__.copy()


class HttpUrl(str):
    """Placeholder type used for URL fields."""

    pass


def Field(*, default=None, default_factory=None):
    """Simplified stand-in for :func:`pydantic.Field`.

    Returns the default value or the result of ``default_factory`` if provided.
    This is sufficient for tests that do not rely on advanced validation.
    """

    if default_factory is not None:
        return default_factory()
    return default
