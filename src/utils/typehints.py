from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PatchableDict(Protocol):
    """Protocol class for type hinting PatchableDict."""

    def as_json(self) -> str:
        """Representation of the dictionary object as JSON."""
        ...

    def as_json_patch(self, *, _path: str = "") -> list[dict[str, Any]]:
        """Generate the JSON patch object based on the snapshot of data created at init."""
        ...

    def as_patch_str(self, *, _path: str = "", **kwargs) -> str:
        """Return the JSON patch object as a string.
        :param **kwargs: kwargs passed on to 'json.dumps'; 'default=str' is set as a default value in **kwargs,
                         overriding this without providing a hook to convert 'ParsedDatetime' to string will cause
                         errors"""
        ...

    def update_snapshot(self) -> None:
        """Update the snapshot to the current version of self."""
        ...


PayloadObject = PatchableDict | dict[str, Any]
