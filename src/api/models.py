import mimetypes

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, Optional, TypeVar

from .protocols import APIResponse


T = TypeVar("T")


@dataclass(slots=True)
class FileUpload:
    file: Path

    def __post_init__(self):
        self.file = Path(self.file)  # enforce type

    @property
    def mime_type(self) -> str:
        """Determine file mimetype"""
        try:
            mime_type, _ = mimetypes.guess_file_type(self.file)  # Python 3.13+
        except AttributeError:
            mime_type, _ = mimetypes.guess_type(self.file)

        if mime_type:
            return mime_type

        return "application/octet-stream"

    def as_dict(self) -> dict:
        """Convert self to dictionary represenation. Used for file uploads."""
        return {
            "file_name": (None, self.file.name),
            "file_content": (self.file.name, self.file.open("rb"), self.mime_type),
        }


@dataclass(slots=True)
class Page(Generic[T]):
    """Page object for paginated endpoints."""
    response: APIResponse
    offset: int
    top: int
    page_num: int

    @property
    def data(self) -> Sequence[T]:
        """Return this page's records as a sequence of T."""
        return self.response.data


class PaginatedResult(Generic[T]):
    """Wraps paginated results allowing iteration over pages or access to flattened results."""

    def __init__(self, pager: Callable[[], Iterator[Page[T]]]) -> None:
        self._pager_func = pager
        self._data_cache: Optional[list[T]] = None
        self._pages_cache: Optional[list[Page[T]]] = None

    def __repr__(self) -> str:
        cls = type(self).__name__
        properties = []

        for name, attr in type(self).__dict__.items():
            if isinstance(attr, property) and not name.startswith("_"):
                try:
                    value = getattr(self, name)
                except Exception as e:
                    value = f"<error: {e}"

                properties.append(f"{name}={value!r}")

        return f"{cls}({', '.join(properties)})"

    @property
    def pages(self) -> Iterator[Page[T]]:
        """Yield 'Page' objects."""
        if self._pages_cache is None:
            self._pages_cache = list(self._pager_func())

        return iter(self._pages_cache)

    @property
    def results(self) -> Iterator[T]:
        """Yields individual records across all pages."""
        for page in self.pages:
            yield from page.data

    @property
    def data(self) -> Sequence[T]:
        """Return all data from pages as a single sequence object (list)."""
        # use cache or create cache to ensure items are not rebuilt on every access
        if self._data_cache is None:
            self._data_cache = list(self.results)

        return self._data_cache

    def refresh_cache(self) -> None:
        """Refresh internal data and page cache."""
        self._data_cache = None
        self._pages_cache = None
