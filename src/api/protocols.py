from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, ContextManager, Optional, Protocol, runtime_checkable

import requests

from requests.adapters import Retry


@runtime_checkable
class TassAPIServer(Protocol):
    """Protocol class for 'TassAPIServer' typing and other such uses."""

    base: str
    key: str
    secret: str
    cmpy_code: str
    token_expire_offset: Optional[int]
    retries: Optional[int]
    status_forcelist: Optional[Sequence[int]]

    @property
    def retry_adapter(self) -> Retry:
        """The 'Retry' adapter that will be attached to the API session."""
        ...


@runtime_checkable
class APITokenData(Protocol):
    """Protocol class for 'APITokenData' typing and other such uses."""

    token: str
    token_expiry_date: datetime
    allowed_companies: list[dict]

    def __post_init__(self):
        """Post Init actions."""
        ...

    def convert_token_expire_date(self, v: str) -> datetime:
        """Convert the token expiration date value from a successful authentication request."""
        ...


class APISession(Protocol):
    """Protocol class for 'APISession' typing and other such uses."""

    server: TassAPIServer

    @property
    def allowed_companies(self) -> Optional[list[dict[str, str]]]:
        """Companies that we are allowed to query."""
        ...

    @property
    def authenticated(self) -> bool:
        """We are authenticated."""
        ...

    @property
    def auth_data(self) -> Optional[APITokenData]:
        """Convenience method for authentication metadata."""
        ...

    @property
    def has_token(self) -> bool:
        """We have a token after authentication."""
        ...

    @property
    def token_expired(self) -> bool:
        """The token has expired."""
        ...

    @property
    def valid_company_code(self) -> bool:
        """The company code declared in the 'TassAPIServer' is one that we have permission to query."""
        ...

    def authenticate(self, *, auth_endpoint: str = "users") -> None:
        """Authenticate to the API."""
        ...

    def parse_request_kwargs(self, **kwargs) -> tuple[dict, dict]:
        """Parse kwargs that are specific to requests. Returns a tuple of request related kwargs and function
        related kwargs."""
        ...

    def prepare_file_upload(self, files: dict[str, Any]) -> ContextManager[dict[str, tuple]]:
        """Context manager for file uploads."""
        ...


@runtime_checkable
class APIResponse(Protocol):
    """Protocol class for 'APIResponse' typing and other such uses."""

    @property
    def r(self) -> requests.Response:
        """The native unwrapped 'requests.Response' object."""
        ...

    @property
    def digest_data(self) -> tuple[Optional[str], Optional[str]]:
        """Digest type and value when a response object has a file stream."""
        ...

    @property
    def filename(self) -> Optional[str]:
        """Remote resource filename where response object has a file stream."""
        ...

    @property
    def has_file_stream(self) -> bool:
        """Response object has a file stream available for download."""
        ...

    @property
    def has_more(self) -> bool:
        """Indicate more data is returnable when paginating endpoints."""
        ...

    @property
    def has_json(self) -> bool:
        """Test response object has JSON."""
        ...

    @property
    def resp_ok(self) -> bool:
        """Test status code is OK by checking 'safe_statuses'"""
        ...

    def json(self, **kwargs) -> Optional[dict[str, Any]]:
        """Return JSON object from response."""
        ...

    def raise_for_status(self) -> None:
        """Raise exceptions when status codes are not  OK."""
        ...


@runtime_checkable
class FileUpload(Protocol):
    file: Path

    @property
    def mime_type(self) -> str:
        """Determine file mimetype"""
        ...

    def as_dict(self) -> dict:
        """Convert self to dictionary represenation. Used for file uploads."""
        ...
