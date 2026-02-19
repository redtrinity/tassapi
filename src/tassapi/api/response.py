from collections.abc import Sequence
from functools import cached_property
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

import requests

from ..utils.datetime_utils import datetime_obj_hook
from ..utils.json_utils import parse_json_with_hooks
from ..utils.request_utils import (
    parse_has_file_stream,
    parse_digest_data_from_response,
    parse_filename_from_response,
    parse_response_error_data,
)

DEFAULT_SAFE_HTTP_OK = set(range(200, 400))


class APIResponse:
    """Custom class that extends/wraps 'requests.Response' functionality.

    Adds:
        self.data - applies a hook to modify date like strings into ParsedDatetime objects
        self.digest_data - convenience property returning the digest type and value from headers if a response
                           has a file stream
        self.filename - convenience property returning the filename of a remote resource if the response has
                        a file stream
        self.has_file_stream - convenience property indicating if the response has a file stream based on header data
        self.has_json - indicates a response has/does not have JSON
        self.has_more - convenience property for paginating indicating if there is more content to paginate; note, this
                        calls an internal hidden method that can also be used elsewhere if a more specific 'has_more'
                        test is required
        self.resp_ok - convenience property for testing a response status code is OK; this allows testing non-standard
                       HTTP status codes that would typically indicate errors but are OK in the context of the API, or
                       status codes that are used to flag 'OK' like behaviour
        self.json - convenience caller for the underlying response.json() method
        self.raise_for_status - re-implements the native requests 'raise_for_status' method so API error data can be
                                included where error data is returned and adds safe status code testing for status
                                codes that fall outside the typical range of OK; this ensures exceptions are only
                                raised when required (uses 'safe_statuses=set(404, 405)' kwarg passed to a request)"""

    def __init__(self, r: requests.Response, *, safe_statuses: Optional[Sequence[int]] = None) -> None:
        self.r = r
        self.safe_statuses = DEFAULT_SAFE_HTTP_OK.union(set(safe_statuses or []))
        self._json_cache: Any = None
        self._json_cached: bool = False

    def __getattr__(self, name: str) -> Any:
        """Custom getattr implementation to return attributes from requests.Response as well as our own."""
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return getattr(self.r, name)

    def __repr__(self) -> str:
        return f"<APIResponse [{self.status_code}]>"

    @cached_property
    def data(self) -> Optional[Sequence[dict[str, Any]]]:
        """Convenience property that calls 'self.json()' for pagination."""
        if not self.has_json:
            return []

        data = parse_json_with_hooks(self.r.json(), hooks=(datetime_obj_hook, ))

        return data

    @property
    def digest_data(self) -> tuple[Optional[str], Optional[str]]:
        """Where available, return the digest type (for example; 'sha-256') and value. This relates only to remote
        file resources that can be downloaded or uploaded."""
        return parse_digest_data_from_response(self.r)

    @property
    def filename(self) -> Optional[str]:
        """Where available, return the filename of the remote resource as indicated by the 'content-disposition'
        header data."""
        return parse_filename_from_response(self.r)

    @property
    def has_file_stream(self) -> bool:
        """Response has a file-stream as indicated by either 'attachment' or 'inline' value in the
        'content-disposition' header value."""
        return parse_has_file_stream(self.r)

    @property
    def has_json(self) -> bool:
        """Indicates the response has JSON; determined by the 'Content-Type' header including 'application/json' in the
        value."""
        return "application/json" in self.headers.get("content-type", "").casefold()

    @property
    def has_more(self) -> bool:
        """Test if the response (when iterating paginated endpoints) has more data in the response. Uses the '$top'
        OData param in the response URL."""
        return self._has_more()

    @property
    def has_raw_resp(self) -> bool:
        """Test if the raw response 'self.r' exists."""
        r = getattr(self, "r", None)
        return r is not None and isinstance(r, requests.Response)

    @property
    def resp_ok(self) -> bool:
        """Check if the response is 'ok' by checking the response status code against a safe list of status codes.
        By default any HTTP status code between HTTP 200-399 is considered OK.
        This differs to 'requests.Response.status_ok'."""
        return self.r.status_code in self.safe_statuses

    def _has_more(self, expected: Optional[int] = None) -> bool:
        """Check if the JSON object in the response may have more data to return when querying a paginated endpoint
        When 'page_len' is explicitly provided, this number is used in the test, when not provided, an attempt is made
        to extract the value from any params in the 'requests.Response.url' attribute.
        :param expected: the number of expected records to return per page"""
        if not self.has_json:
            return False

        params = parse_qs(urlparse(self.r.url).query)

        page_len = len(self.json())  # actual number of records; relies on the response JSON already being an array
        expected = expected or int(params["$top"][0])

        return page_len == expected

    def json(self, **kwargs) -> Optional[dict[str, Any]]:
        """Access raw JSON from the requests response; no hooks or other processing applied unless specified in
        kwargs."""
        return self.r.json(**kwargs)

    def raise_for_status(self) -> None:
        """Customise the 'requests.Response.raise_for_status()' to also include any additional error message data from
        the API response, and only raise exceptions when the status code is not considered a 'safe' status code.
        :param r: response object"""
        if not self.resp_ok:
            http_error_msg, err_type = "", None

            if isinstance(self.r.reason, bytes):
                # We attempt to decode utf-8 first because some servers
                # choose to localize their reason strings. If the string
                # isn't utf-8, we fall back to iso-8859-1 for all other
                # encodings. (See PR #3538)
                try:
                    reason = self.r.reason.decode("utf-8")
                except UnicodeDecodeError:
                    reason = self.r.reason.decode("iso-8859-1")
            else:
                reason = self.r.reason

            if 400 <= self.r.status_code < 500:
                err_type = "Client Error"
            elif 500 <= self.r.status_code < 600:
                err_type = "Server Error"

            if err_type is not None:
                http_error_msg = f"{self.r.status_code} {err_type}: {reason} for url: {self.r.url}"

            if http_error_msg:
                api_err_data = parse_response_error_data(self.r) if self.has_raw_resp else None

                if api_err_data is not None:
                    suffix = "API error data:\n{title} {detail}\n{errors}\n{message}".format(**api_err_data)
                    http_error_msg = f"{http_error_msg}\n{suffix}"

                raise requests.exceptions.HTTPError(http_error_msg)
