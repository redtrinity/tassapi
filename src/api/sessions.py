import inspect
import logging

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, ContextManager, Optional
from urllib.parse import urlparse

import requests

from requests.adapters import HTTPAdapter, Retry
from ..utils.request_utils import build_user_agent, urljoin

log = logging.getLogger(__name__)


REQUEST_PARAM_NAMES = tuple(
    name for name in inspect.signature(requests.Session.request).parameters if not name == "self"
)


@dataclass
class TassAPIServer:
    """Server Configuration."""

    base: str
    key: str
    secret: str
    cmpy_code: str
    token_expire_offset: Optional[int] = field(default=60)
    attachment_dest: Optional[Path] = field(default=Path("/tmp"))

    retries: Optional[int] = field(default=5)
    status_forcelist: Optional[Sequence[int]] = field(default_factory=lambda: [429])

    @property
    def retry_adapter(self) -> Retry:
        """Return a new instance of requests.adapters.Retry with retry settings applied."""
        return Retry(total=self.retries, status_forcelist=self.status_forcelist)


@dataclass
class APITokenData:
    """Dataclass to hold token data from authentication response."""

    token: str
    token_expiry_date: datetime
    allowed_companies: list[dict]

    def __post_init__(self):
        self.token_expiry_date = self.convert_token_expire_date(self.token_expiry_date)

    def convert_token_expire_date(self, v: str) -> datetime:
        """Convert the token expire date string to native datetime.
        :param v: string"""
        if isinstance(v, datetime):
            return v

        if isinstance(v, str):
            # normalize to datetime, normalize UTC first
            return datetime.fromisoformat(v.replace("Z", "+00:00"))


class PreserveAuthenticationAdapter(HTTPAdapter):
    """Send a request while preserving 'Authorization' across same-origin redirects. This changes the
    default behaviour of requests where it does not always preserve 'Authorization' header on redirects.

    Stores the original URL and Authorization header on first send, restores Authorization on same-origin
    redirects when the server omits it, and cleans up the temporary attributes on the final (non-redirect)
    response."""

    def _parse_origin(self, url: str) -> tuple[str, str, Optional[int]]:
        """Parses the url into scheme, hostname, and port for comparison"""
        p = urlparse(url)
        scheme = p.scheme.lower()
        hostname = p.hostname.lower() if p.hostname else ""
        port = p.port if p.port is not None else (80 if scheme == "http" else 443 if scheme == "https" else None)

        return (scheme, hostname, port)

    def _is_same_origin(self, url_1: str, url_2: str) -> bool:
        """Returns True/False if url_1 and url_2 have the same scheme, hostname, port, etc.
        :param url_1: first url to compare
        :param url_2: second url to compare"""
        url1 = self._parse_origin(url_1)
        url2 = self._parse_origin(url_2)

        return url1 == url2

    def send(self, request, **kwargs):
        # on the first request, store the original url and auth in request attributes for thread safety
        if not hasattr(request, "_original_request_url"):
            request._original_request_url = request.url
            request._original_auth = request.headers.get("Authorization")

        # on redirect requests, restore the auth if the authorization header is missing
        if request.url != getattr(request, "_original_request_url"):
            # check origin before applying auth header
            if request._original_auth and "Authorization" not in request.headers:
                if self._is_same_origin(request._original_request_url, request.url):
                    request.headers["Authorization"] = request._original_auth

        response = super().send(request, **kwargs)

        # reset original url and auth after final response
        if not response.is_redirect:
            for attr in ["_original_request_url", "_original_auth"]:
                if hasattr(request, attr):
                    delattr(request, attr)

        return response


class APIAuthenticationException(Exception):
    def __init__(self, r: requests.Response) -> None:
        self.message = f"Error: No authentication response. HTTP {r.status_code} for {r.url}"
        log.error(self.message)

        super().__init__(self.message)


class APISession(requests.Session):
    """Extend the requests.Session class with additional functionality for authentication and global session
    attributes/settings."""

    _default_headers = {
        "Accept": "application/json",
        "User-Agent": build_user_agent("com.github.redtrinity.tassapi", version="1.0.0"),
    }

    def __init__(self, server: TassAPIServer) -> None:
        super().__init__()
        self._metadata: dict[str, Any] = {}

        self.server = server
        self.headers.update(self._default_headers)
        self.mount("https://", PreserveAuthenticationAdapter(max_retries=self.server.retry_adapter))

    @property
    def allowed_companies(self) -> Optional[list[dict[str, str]]]:
        """Allowed companies data from the authentication response."""
        if self.auth_data is not None:
            return self.auth_data.allowed_companies

        return None

    @property
    def authenticated(self) -> bool:
        """Session is authenticated."""
        return self.has_token and not self.token_expired

    @property
    def auth_data(self) -> Optional[APITokenData]:
        """Shortcut to authentication data stored in an internal metadata attribute."""
        data = self._metadata.get("auth_data")

        return data or None

    @property
    def has_token(self) -> bool:
        """A token has been received after authenticating."""
        return bool(self.headers.get("Authorization", False))

    @property
    def token_expired(self) -> bool:
        """A token has expired."""
        # no auth data implies not authenticated, so technically token has expired
        if self.auth_data is None:
            return True

        adjusted_expire_time = self.auth_data.token_expiry_date - timedelta(seconds=self.server.token_expire_offset)

        # when the adjusted expire time IS less than datetime.now(), this must be False in order to not be expired
        expired = not adjusted_expire_time <= datetime.now()

        return expired

    @property
    def valid_company_code(self) -> bool:
        """Once authenticated, validate the company code from the server instance is one that the API
        returns."""
        if self.allowed_companies:
            for cmpy in self.allowed_companies:
                return self.server.cmpy_code in cmpy.get("cmpy_code", "")

        return False

    def authenticate(self, *, auth_endpoint: str = "users") -> None:
        """Performs initial authentication.
        :param auth_endpoint: string value of endpoint used for authentication; default is 'users'"""
        url = urljoin(self.server.base, auth_endpoint)
        payload = self._auth_payload()
        response = requests.post(url, headers=self.headers, json=payload)

        try:
            auth_data = self._make_token(response.json())
        except Exception:
            raise APIAuthenticationException(response)

        if auth_data is not None:
            auth_headers = {"Authorization": f"Bearer {auth_data.token}"}
            self.headers.update(auth_headers)
            self._metadata["auth_data"] = auth_data

    def parse_request_kwargs(self, **kwargs) -> tuple[dict, dict]:
        """Separate kwargs for the requests.Session.request call from other kwargs used elsewhere."""
        req_kwargs = {}
        func_kwargs = {}

        for key, value in kwargs.items():
            if key in REQUEST_PARAM_NAMES:
                req_kwargs[key] = value
            else:
                func_kwargs[key] = value

        return (req_kwargs, func_kwargs)

    def prepare_file_upload(self, files: dict[str, Any]) -> ContextManager[dict[str, tuple]]:
        """Create a context manager for handling file uploads.
        :param files: files dictionary, must conform to the POST Multiple Multipart-Encoded FIles documented here:
            https://docs.python-requests.org/en/latest/user/advanced/#advanced"""
        if not isinstance(files, dict):
            raise ValueError(f"'files': expected dictionary object, got {type(files)}")

        @contextmanager
        def upload_context() -> Iterator[dict[str, tuple]]:
            """Actions to perform when the context is closed."""
            try:
                files_dict = dict(files)
            except Exception as e:
                raise ValueError(f"failed to prepare file upload: {e}") from e
            finally:
                # close file like objects
                for item in files_dict.values():
                    # item is a tuple like (filename, file_obj, mime_type)
                    if len(item) > 1 and hasattr(item[1], "close"):
                        item[1].close()

        return upload_context()

    def set_content_type_header(self, method: str, *, req_kw: dict[str, Any]) -> None:
        """Set the value for 'Content-Type' header based on HTTP method and payload.
        :param method: HTTP method performed, for example 'PATCH'
        :param req_kw: request keyword arguments"""
        headers = req_kw.setdefault("headers", {})  # current headers from the request or empty dict

        if "files" in req_kw:
            # pop 'Content-Type' out so that requests directly sets correct value for multipart/form-data uploads
            headers.pop("Content-Type", None)
        elif method == "patch":
            headers["Content-Type"] = "application/json-patch+json"
        elif method in ("post", "put"):
            headers["Content-Type"] = "application/json"
        else:
            headers.setdefault("Content-Type", "application/json")

    def _auth_payload(self) -> dict:
        """Authentication payload."""
        return {"clientKey": self.server.key, "clientSecret": self.server.secret}

    def _make_token(self, data: dict) -> Optional[APITokenData]:
        """Return the token data as an instance of APITokenData."""
        token_data_keys = ["token", "token_expiry_date", "allowed_companies"]

        try:
            return APITokenData(**{k: data[k] for k in token_data_keys})
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError("Invalid token structure") from e

        return None
