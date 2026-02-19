import platform
import posixpath
import re

from base64 import b64decode
from email.message import Message
from typing import Any, Optional
from urllib.parse import quote, unquote, urlparse, urlunparse

import requests


def build_user_agent(name: str, *, version: str):
    """Build a user agent string.
    :param name: intended name of the user-agent, for example 'tassapi-ua'
    :param version: version of the user-agent, for example '1.0.0'"""
    python_info: tuple[Optional[str], Optional[str]] = (platform.python_implementation(), platform.python_version())
    system_info: tuple[Optional[str], Optional[str]] = (platform.system(), platform.release())
    py_extras = "/".join(x for x in python_info if x is not None)
    os_extras = "/".join(x for x in system_info if x is not None)

    return f"{name}/{version} {py_extras} {os_extras}"


def urljoin(base: str, *paths) -> str:
    """A custom implementation of urljoin that parses a URL into component parts, joins paths to any path
    value from the base path, normalizes the path value so any redundant '/' characters are removed, then
    rejoins the url together into a new url.
    :param base: base of the url; for example: 'https://example.org/api/v1'
    :param *paths: additional values to be used as paths, for example 'users', 'information'"""
    parsed_base = urlparse(base)
    safe_paths = [quote(str(p).strip("/ \n\r\t")) for p in paths if p]
    combined_path = posixpath.join(parsed_base.path, *safe_paths)
    combined_path = posixpath.normpath(combined_path)  # normalize '..' and '.'

    if not combined_path.startswith("/"):
        combined_path = f"/{combined_path}"

    combined_path = re.sub(r"/{2,}", "/", combined_path)  # normalize two or more '/' to single '/'

    if combined_path.endswith("/"):
        combined_path = combined_path.rstrip("/")

    url = urlunparse(parsed_base._replace(path=combined_path))  # rebuild the full URL with normalized path

    return url


def parse_response_error_data(r: requests.Response) -> Optional[dict[str, Any]]:
    """Parse any response data returned by the API and return a dictionary of values."""
    # error_attrs = ("status", "title", "detail", "errors", "message")
    error_attrs = ("title", "detail", "errors", "message")

    try:
        err_data = r.json()
    except Exception:
        return None

    if not err_data:
        return None

    return {attr: err_data.get(attr, None) for attr in error_attrs}


def parse_digest_data_from_response(r: requests.Response) -> Optional[tuple[str, str]]:
    """Parse the digest type (i.e. SHA-256) and digest value from the headers of the response object.
    The digest value in the 'Digest' header is expected to be a base64 encoded string.
    :param r: response object"""
    digest = r.headers.get("Digest")

    if not digest:
        return (None, None)

    digest_type, digest_value = digest.split("=", 1)
    digest_value = b64decode(digest_value).hex()

    return (digest_type, digest_value)


def parse_filename_from_response(r: requests.Response) -> Optional[str]:
    """Parse the remote filename from header data from the response object.
    :param r: response object"""
    try:
        msg_params = ("filename", "filename*")
        content_disposition = r.headers.get("content-disposition")

        if not content_disposition:
            return None

        # use email.message.Message to make parsing the header simpler
        msg = Message()
        msg["Content-Disposition"] = content_disposition

        for msg_param in msg_params:
            filename = msg.get_param(msg_param, header="Content-Disposition")

            # RFC 5987 style 'filename*'
            if "*" in msg_param:
                if "''" in filename:
                    _, encoded_fn = filename.split("''", 1)
                    filename = unquote(encoded_fn.strip("\"'"))

            return filename.strip("\"'")
        return None
    except Exception:
        return None


def parse_has_file_stream(r: requests.Response) -> bool:
    """Response has headers indicating a file stream exists."""
    indicators = ("attachment", "inline")
    content_disposition = r.headers.get("content-disposition", "").lower()
    has_fs = any(indicator in content_disposition for indicator in indicators)

    return has_fs


def merge_odata_filter_param(fltr: str, *, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Merge an OData filter string into existing params.
    :param fltr: OData filter string, for example 'doe ge {date} or dol eq null or dol ge {date}'
    :param kwargs: dictionary of params"""
    params = dict(kwargs.get("params", {}))
    exst_fltr = params.get("$filter", "").strip()
    params["$filter"] = f"({exst_fltr}) and ({fltr})" if exst_fltr else fltr
    kwargs["params"] = params

    return kwargs
