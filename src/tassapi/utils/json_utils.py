from collections.abc import Callable, Mapping, Sequence
from typing import Any, Optional

from .models import PatchableDict
from .json_patch_utils import _json_diff


def json_patch(from_obj: Any, to_obj: Any, *, path: str = "") -> list[dict[str, Any]]:
    """Create an RFC 6902 JSON Patch from two Python objects.
    :param from_obj: from object
    :param to_obj: to object
    :param path: path string"""
    return _json_diff(from_obj, to_obj, path=path)


def parse_json_with_hooks(obj: Any, *, hooks: Optional[Sequence[Callable[[Any], Any]]] = None) -> Any:
    """Convert a 'requests.Response.json()' result into a 'PatchableDict' instance. Expects already decoded
    JSON data, not a JSON string.
    Every mapping becomes a 'PatchableDict', hooks are applied to each mapping before recursion. Only the
    returned root 'PatchableDict' is snapshotted by default (covers the whole tree).
    Returns the same shape as input but with 'dict' objects replaced by 'PatchableDict' objects.
    :param obj: parsed JSON
    :param hooks: a sequence of callables applied to each mapping (typically mutates in place)"""
    def _apply_hooks(d: dict[str, Any]) -> None:
        if hooks is None:
            return
        for hook in hooks:
            if callable(hook):
                hook(d)

    def _walk(x: Any) -> Any:
        if isinstance(x, Mapping):
            d = dict(x)
            _apply_hooks(d)

            for k, v in list(d.items()):
                d[str(k)] = _walk(v)

            return PatchableDict(d)

        if isinstance(x, list):
            return [_walk(v) for v in x]

        if isinstance(x, tuple):
            return tuple(_walk(v) for v in x)

        return x

    return _walk(obj)
