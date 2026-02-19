import json

from functools import cached_property
from typing import Any, Optional

from ..api.worker import TassWorker
from ..api.protocols import APISession
from ..utils.datetime_utils import timestamp_now_as_str, today_midnight_ts, today_as_str
from ..utils.json_patch_utils import _json_diff
from ..utils.request_utils import merge_odata_filter_param


class EndpointBase(TassWorker):
    """Endpoint base class.

        - Inherits 'TassWorker' for all HTTP work.
        - Inherited by endpoint class implementations to access the helper methods and properties that might be
        required in various endpoint implementations.
        - Provides cached properties that return several date objects as string values, such as:
            - self.today - returns YYYY-mm-dd formatted string
            - self.today_midnight - returns YYYY-mm-ddT00:00:00.000 formatted string
            - self.timestamp_now(fmt=fmt) - returns YYYY-mm-ddTHH:MM:SS.fff formatted string; 'fmt' is an optional
                                            datetime format string template

    :param session: instance of APISession; this handles authentication for all endpoints that inherit this class
    :param endpoint: an optional string representing the endpoint path, this is generally a required value, but there
                     are circumstances such as sub-endpoint implementations where this might not be required (when
                     implementing an endpoint class, the 'endpoint' param should be treated as required where it is
                     required for that implementation)"""

    def __init__(self, session: APISession, *, endpoint: Optional[str] = None) -> None:
        super().__init__(session)
        self.endpoint = endpoint  # this is generally a required value, but sometimes it's optional

    @cached_property
    def today(self) -> str:
        """Today's date as a string, cached. Returns 'YYYY-mm-dd' formatted date string."""
        return today_as_str()

    @cached_property
    def today_midnight(self) -> str:
        """Today's date as datetime string, cached. Returns 'YYYY-mm-ddT00:00:00.000' formatted datetime string.
        Microseconds precision is capped to 3, if microseconds are not required, trim the last four characters '.000'"""
        return today_midnight_ts()

    def as_json_patch(self, from_obj: Any, to_obj: Any) -> list[dict[str, Any]]:
        """Create a JSON patch object for patching data where JSON patch is required."""
        return _json_diff(from_obj, to_obj)

    def as_patch_string(self, from_obj: Any, to_obj: Any) -> str:
        """Return the JSON patch object as a string."""
        out = self.as_json_patch(from_obj, to_obj)

        return json.dumps(out, default=str)

    def merge_filter_param(self, fltr: str, *, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Convenience call '..utils.request_utils import merge_odata_filter_param'"""
        return merge_odata_filter_param(fltr, kwargs=kwargs)

    def timestamp_now(self, fmt: Optional[str] = None) -> str:
        """Current datetime as a datetime string, cached. Returns 'YYYY-mm-ddTHH:MM:SS.fff' formatted datetime string.
        Microseconds precision is capped to 3, if microseconds are not required, trim the last four characters '.fff'
        :param fmt: optional format string template; for example '%Y-%m-%dT%H:%M:%S.%f' (default)"""
        return timestamp_now_as_str(fmt=fmt)
