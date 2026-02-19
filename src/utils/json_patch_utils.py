from collections.abc import Mapping, Sequence
from typing import Any


def _escape_token(tkn: str) -> str:
    """RFC 6901 escaping"""
    return tkn.replace("~", "~0").replace("/", "~1")


def _join(p: str, k: str) -> str:
    """Join path with key.
    :param p: path
    :param k: key"""
    k = _escape_token(k)

    return f"{p}/{k}" if p else f"/{k}"


def _json_diff(a: Any, b: Any, path: str = "") -> list[dict[str, Any]]:
    """Generate diffs between 'a' (from) and 'b' (to), where both are dictionaries.
    :param a: from object
    :param b: to object
    :param path: path"""
    ops: list[dict[str, Any]] = []

    # no changes
    if a == b:
        return ops

    # mapping vs mapping
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        a_keys = set(a.keys())
        b_keys = set(b.keys())

        # removals
        for k in sorted(a_keys - b_keys):
            p = _join(path, str(k))
            ops.append({"op": "test", "path": p, "value": a[k]})
            ops.append({"op": "remove", "path": p})

        # additions
        for k in sorted(b_keys - a_keys):
            p = _join(path, str(k))
            ops.append({"op": "add", "path": p, "value": b[k]})

        # recurse shared/common keys (between a/b)
        for k in sorted(a_keys & b_keys):
            ops.extend(_json_diff(a[k], b[k], path=_join(path, str(k))))

        return ops

    # sequences (list/tuples)
    # skip strings/bytes/bytearrays because these are also sequences
    if (
        isinstance(a, Sequence)
        and isinstance(b, Sequence)
        and not isinstance(a, (str, bytes, bytearray))
        and not isinstance(a, (str, bytes, bytearray))
    ):
        ops.append({"op": "test", "path": path or "", "value": a})
        ops.append({"op": "replace", "path": path or "", "value": b})

        return ops

    # anything else, replace scalar/mismatched types
    ops.append({"op": "test", "path": path or "", "value": a})
    ops.append({"op": "replace", "path": path or "", "value": b})

    return ops
