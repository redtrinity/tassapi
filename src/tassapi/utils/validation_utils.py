import hashlib

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Optional

from .string_utils import oxford_join


def raise_for_digest_error(fp: Path, *, digest_type: str, digest_value: str, chunk_size: int = 8192) -> None:
    """Validate the digest of a downloaded file. Raises a ValueError exception if the digests do not match.
    :param fp: file path
    :param digest_type: the digest type; for example 'SHA-256'
    :param digest_value: the expected digest value"""
    h = hashlib.new(digest_type)

    with fp.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)

    actual_digest = h.hexdigest().casefold()
    target_digest = digest_value.casefold()

    if not actual_digest == target_digest:
        raise ValueError(
            f"{str(fp)=} digest value '{actual_digest}' does not match expected value '{target_digest}'"
        )


def raise_for_reqd_attrs(obj: dict[str, Any], *, reqd_attrs: Sequence[str], param_name: Optional[str] = None) -> None:
    """Raise a ValueError exception when required attributes are missing from an object.
    :param obj: dictionary object
    :param param_name: paramter name to include in the exception
    :param reqd_attrs: required attributes that should exist in 'obj'"""
    missing_attrs = tuple(k for k in reqd_attrs if k not in obj.keys())

    if missing_attrs:
        attr_str = oxford_join("and", *missing_attrs)
        param_name = f"{param_name!r}" if param_name else ''
        err_msg = f"{param_name} is missing required attribute{'s' if len(missing_attrs) > 1 else ''}: {attr_str}"

        raise ValueError(err_msg)
