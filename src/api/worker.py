import logging

from collections.abc import Callable, Iterator
from functools import wraps
from pathlib import Path
from typing import Optional, TypeVar

import requests

from .protocols import APISession
from .response import APIResponse
from .models import FileUpload, Page, PaginatedResult
from ..utils.request_utils import urljoin
from ..utils.typehints import PayloadObject
from ..utils.validation_utils import raise_for_digest_error, raise_for_reqd_attrs

log = logging.getLogger(__name__)

T = TypeVar("T")


def request(method: str) -> Callable:
    """Perform a specific HTTP request.
    Decorates the relevant HTTP methods in the 'Worker' class."""
    method = method.casefold()

    def wrapper(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapped_fn(self, *args, **kwargs) -> requests.Response:
            if not self.session.authenticated:
                self.session.authenticate()

            path = urljoin(*args) if args else None
            url = urljoin(self.session.server.base, self.session.server.cmpy_code, self.endpoint, path)
            print(f"@request.{url=}")
            req_kw, fnc_kw = self.session.parse_request_kwargs(**kwargs)
            has_patch_obj = bool(req_kw.get("data", None))
            has_files = bool(req_kw.get("files"))
            safe_statuses = fnc_kw.get("safe_statuses", None)
            self.session.set_content_type_header(method, req_kw=req_kw)

            # seems the TASS API only supports a JSON string, so converft
            if has_patch_obj and method == "patch":
                patch_obj = req_kw["data"]

                # if 'patch_obj' doesn't have 'as_patch_str' as an attribute, presume it's ok to pass as is
                try:
                    req_kw["data"] = patch_obj.as_patch_str()
                except AttributeError:
                    pass

            if has_files:
                files = req_kw["files"]

                with self.session.prepare_file_upload(files) as upload:
                    req_kw["files"] = upload
                    resp = self.session.request(method, url, **req_kw)
            else:
                resp = self.session.request(method, url, **req_kw)

            wrapped_response = APIResponse(resp, safe_statuses=safe_statuses)
            wrapped_response.raise_for_status()

            return wrapped_response

        return wrapped_fn

    return wrapper


class TassWorker:
    """Implements underlying methods for the new TASS API rolled out in TASS v2026.01.201 on 2026-02-03.

    This class should be used as the parent class of any endpoint class created, a number of convenience methods as
    well as methods representing the HTTP methods are present here.

    Convenience methods:
        - 'create' create a new object; specifically has 'payload' param which is injected to 'kwargs["json"]'
        - 'download' download a remote file; has various params to control where the file is downloaded to and disable
           checksum validation
        - 'upload' upload a local file to a remote path; requires an instance of 'FileUpload' representing the file
           being uploaded
        - 'paginate' iterates endpoints that have paged responses; returns a 'PaginatedResult' instance where parsed
          data (to JSON) is accessible through .data; result data can be paginated through .results, and each page
          response object can be accessed through .pages

    All HTTP methods will return an instance of APIResponse (this wraps the requests.Response object) or raise
    exceptions if the HTTP status code for the response is one indicative of an error.
    In circumstances where an API response returns a status code that is typically indicative of an error that would
    raise exceptions, the request can have the 'safe_statuses=(...)' param passed with a sequence of HTTP status code
    integers that are 'safe' to ignore when 'APIResponse.raise_for_status' is called. By default all HTTP 200-399
    statuses are considered safe."""

    def __init__(self, session: APISession) -> None:
        self.session = session

    def create(self, *args, payload: PayloadObject, validate_keys: Optional[tuple[str, ...]] = None, **kwargs):
        """Convenience method for creating a new resource in an endpoint or specified URL.
        :param *args: optional values for the resource path; do not include the endpoint value (automatically handled)
        :param payload: payload object (dictionary or PatchableDict)
        :param validate_keys: a tuple (strings) of attribute names that are required when creating a new object in
                              the endpoint/path; if no value provided, no validation performed"""
        if validate_keys is not None:
            raise_for_reqd_attrs(payload, reqd_attrs=validate_keys, param_name="payload")

        kwargs.pop("json", None)
        kwargs.setdefault("json", payload)
        return self._post(*args, **kwargs)

    @request("DELETE")
    def _delete(self, *args, **kwargs) -> requests.Response:
        """Perform HTTP 'DELETE'."""
        ...

    def download(
        self,
        *args,
        dest: Optional[Path] = None,
        out_fn: Optional[str] = None,
        chunk_size: Optional[int] = None,
        validate_checksum: Optional[bool] = True,
        **kwargs
    ) -> tuple[requests.Response, Optional[Path]]:
        """Download a file. A URL path must be presented in order for the download to occur. A value must also
        be presented for 'dest' (where the file will be downloaded to). This destination directory must exist.
        :param *args: resource path componets
        :param dest: override the session.server.attachment_dest attribute with an existing directory the file will be
                     downloaded into
        :param out_fn: optionally override the remote filename with a string filename value
        :param chunk_size: an optional integer to use as the chunk size when iterating over the file object
        :param validate_checksum: validate the checksum digest of the file against the checksum digest of the
                                  downloaded file"""
        r = self._get(*args, safe_statuses=set(range(0, 999)), **kwargs)

        # handle circumstances where the response doesn't have a file stream because there is no remote file
        if not r.has_file_stream:
            log.error(f"no file stream detected for '{r.url}'")
            return (r, None)

        dest = dest or self.session.server.attachment_dest
        out_fn = out_fn or r.filename
        fn = dest.joinpath(out_fn)

        with fn.open("wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size or 8192):
                f.write(chunk)

        if validate_checksum:
            digest_type, digest_value = r.digest_data
            raise_for_digest_error(fn, digest_type=digest_type, digest_value=digest_value)

        return (r, fn)

    def upload(self, *args, fp: Path, **kwargs):
        """Convenience method for uploading a file to an endpoint/resource path.
        The file path 'fp' is converted to an instance of 'FileUpload' which contains a helper method to
        determine best possible mimetype and a helper method that generates the correct dictionary object
        for the 'files' param for posting. Providing 'files' in the kwargs is not recommended and will raise
        an error if present.
        :param path: URL path; the API base url and endpoint is not required; for example:
                                     'employees/{emp_code}/notes/standard/{note_uid}/attachments'
        :param fp: file path"""
        if "files" in kwargs:
            raise ValueError("'files' cannot be use in this method")

        file = FileUpload(file=fp)
        kwargs.setdefault("files", file.as_dict())

        return self._post(*args, **kwargs)

    @request("GET")
    def _get(self, *args, **kwargs) -> requests.Response:
        """Perform HTTP 'GET'."""
        ...

    def paginate(self, *args, **kwargs) -> PaginatedResult[T]:
        """Paginate an endpoint that supports OData style '$top'/'$skip'. Returns a PaginatedResult where:
            - .pages yields Page[T] (each page contains the 'APIResponse')
            - .results yields T across all pages
            - .data materializes all results as a list

        :param top: maximum number of records per page returned in the response
        :param offset: the number of records to advance/offset by on each pagination, this is used after the first
                       page iteration and replaces the initial '$skip' value for all subsequent page iterations
        :param skip: how many records to initially skip from; this defaults to 0 (skip no records); this value is
                     overridden by 'offset' after the first page iteration"""
        top, offset, skip = 100, 100, 0

        # snapshot base params once; keeps other OData params stable
        base_params = dict(kwargs.get("params") or {})
        base_params.setdefault("$top", top)
        base_params.setdefault("$skip", skip)

        def pager() -> Iterator[Page[T]]:
            # local per iteration state
            current_skip = int(base_params["$skip"])
            page_top = int(base_params["$top"])
            page = 0

            while True:
                # build params for this request; keep everything from 'base_params'
                new_params = dict(base_params)
                new_params["$skip"] = current_skip

                # build kwargs for this request; keep everything from kwargs but inject params for this request
                req_kw = dict(kwargs)
                req_kw["params"] = new_params

                resp = self._get(*args, **req_kw)  # should return 'APIResponse'

                yield Page(response=resp, offset=current_skip, top=page_top, page_num=page)

                if not resp.has_more:
                    break

                current_skip += offset
                page += 1

        return PaginatedResult(pager)

    @request("PATCH")
    def _patch(self, *args, **kwargs) -> requests.Response:
        """Perform HTTP 'PATCH'."""
        ...

    @request("POST")
    def _post(self, *args, **kwargs) -> requests.Response:
        """Perform HTTP 'POST'."""
        ...

    @request("PUT")
    def _put(self, *args, **kwargs) -> requests.Response:
        """Perform HTTP 'PUT'."""
        ...
