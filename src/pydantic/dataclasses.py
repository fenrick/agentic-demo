from dataclasses import dataclass as std_dataclass


def dataclass(_cls=None, **kwargs):
    """Proxy to :func:`dataclasses.dataclass` used in tests."""

    def wrap(cls):
        return std_dataclass(**kwargs)(cls)

    return wrap(_cls) if _cls is not None else wrap
