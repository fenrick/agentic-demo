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


class HttpUrl(str):
    """Placeholder type used for URL fields."""

    pass
