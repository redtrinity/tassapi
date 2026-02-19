import copy
import json

from typing import Any

from .json_patch_utils import _json_diff
from .datetime_utils import ParsedDatetime

__all__ = [
    "ParsedDatetime",
    "PatchableDict",
]


class PatchableDict(dict):
    """Basic dictionary subclass. Convenience wrapper to extend 'dict' functionality with JSON patch ops data
    based on self + other copy of self.

    Usage:
        Initialize instance (snapshot of state at instantiation is made):
            d = 'PatachableDict({"name": "Jane", "surname": "Citizen"})'
        Modify instance:
            d["surname"] = "Appleseed"
        Generate patch:
            d.as_json_patch()
        """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # create a snapshot of self that is not an instance of 'PatchableDict'; this is used for comparing to self
        self._snapshot: dict[str, Any] = copy.deepcopy(dict(self))

    def as_json(self) -> str:
        """Representation of the dictionary object as JSON."""
        return json.dumps(self, default=str)

    def as_json_patch(self, *, _path: str = "") -> list[dict[str, Any]]:
        """Generate the JSON patch object based on the snapshot of data created at init."""
        return _json_diff(self._snapshot, self, _path)

    def as_patch_str(self, *, _path: str = "", **kwargs) -> str:
        """Return the JSON patch object as a string.
        :param **kwargs: kwargs passed on to 'json.dumps'; 'default=str' is set as a default value in **kwargs,
                         overriding this without providing a hook to convert 'ParsedDatetime' to string will cause
                         errors"""
        kwargs.setdefault("default", str)
        return json.dumps(self.as_json_patch(_path=_path), **kwargs)

    def update_snapshot(self) -> None:
        """Update the snapshot to the current version of self."""
        self._snapshot = copy.deepcopy(dict(self))
