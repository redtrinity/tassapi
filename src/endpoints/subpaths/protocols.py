from typing import Protocol, runtime_checkable


@runtime_checkable
class SubPath(Protocol):
    """SubPath protocol class for type checking, etc."""

    path: str
