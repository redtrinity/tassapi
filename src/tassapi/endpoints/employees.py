from pathlib import Path
from typing import Optional

from .base import EndpointBase
from .options.employees import EmployeeOptions
from .subpaths import NotesSubPaths, PhotosSubPath, UDAreasSubPath
from ..api.protocols import APISession
from ..utils.typehints import PayloadObject


class EmployeeNotes(EndpointBase):
    new_obj_keys = ("note_cat", "note_text", "note_date")

    def __init__(self, session: APISession, endpoint: str, note_type: Optional[str] = None) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = NotesSubPaths.confidential if note_type == "confidential" else NotesSubPaths.standard

    def create(self, emp_code: str, payload: PayloadObject, **kwargs):
        """Create an employee note.
        :param emp_code: employee code
        :param payload: note payload; required keys: 'note_cat', 'note_text', 'note_date'"""
        return super().create(emp_code, self.subpath.path, payload=payload, validate_keys=self.new_obj_keys, **kwargs)

    def get(self, emp_code: str, note_uid: str, **kwargs):
        """Get a note for an employee.
        :param emp_code: employee code
        :param note_uid: note uid"""
        return self._get(emp_code, self.subpath.path, note_uid, **kwargs)

    def get_all(self, emp_code: str, **kwargs):
        """Get all notes for a given employee."""
        return self.paginate(emp_code, self.subpath.path, **kwargs)

    def get_attachments(self, emp_code: str, note_uid: str, **kwargs):
        """Get attachments for a given note. This does not download the attachment but returns attachment information
        such as file name, file size, date uploaded, and the 'attach_id' which is required to download an attachment.
        :param emp_code: employee code
        :param note_uid: note uid"""
        return self._get(emp_code, self.subpath.path, note_uid, self.subpath.attachments.path, **kwargs)

    def download_attachment(
        self,
        emp_code: str,
        note_uid: str,
        attach_id: str,
        *,
        dest: Optional[Path] = None,
        out_fn: Optional[str] = None,
        **kwargs
    ):
        """Download an attachment.
        :param emp_code: employee code
        :param note_uid: note uid
        :param attach_id: attachment code
        :param dest: optionally overried the default directory where content will be stored"""
        paths = (emp_code, self.subpath.path, note_uid, self.subpath.attachments.path, attach_id)
        return super().download(*paths, dest=dest, out_fn=out_fn, **kwargs)

    def upload_attachment(
        self,
        emp_code: str,
        note_uid: str,
        *,
        fp: Path,
        **kwargs
    ):
        """Upload an attachment.
        :param emp_code: employee code
        :param note_uid: note uid
        :param fp: path object"""
        paths = (emp_code, self.subpath.path, note_uid, self.subpath.attachments.path)
        return super().upload(*paths, fp=fp, **kwargs)


class EmployeePhotos(EndpointBase):
    """Employee photos endpoint."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = PhotosSubPath

    def download_photos(self, emp_code: str, *, dest: Optional[Path] = None, out_fn: Optional[str] = None, **kwargs):
        """Downloads the ZIP file containing the photo and thumbnail."""
        return super().download(emp_code, self.subpath.path, dest=dest, out_fn=out_fn)

    def get_change_history(self, change_key: Optional[str] = None, **kwargs):
        """Get photo change history. If 'change_key' is not provided, then all changes are returned; if a value
        for 'change_key' is provided, then those specific changes are returned.

        To get valid values for 'change_key' this method must be called without a value provided.
        :param change_key: optional change key"""
        paths = (self.subpath.path, self.subpath.changes.path, change_key)
        return self._get(*paths, **kwargs)

    def upload_photo(
        self,
        emp_code: str,
        *,
        fp: Path,
        **kwargs
    ):
        """Upload a employee photo.
        :param emp_code: employee code
        :param fp: path object"""
        paths = (emp_code, self.subpath.path)
        return super().upload(*paths, fp=fp, **kwargs)


class EmployeeUDAreas(EndpointBase):
    """Employee UD areas endpoint."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = UDAreasSubPath

    def create(self, emp_code: str, area_code: str, *, payload: PayloadObject, **kwargs):
        """Create data in a UD area object for a employee. The specific UD area must already be configured in Employee
        Setup.
        :param emp_code: employee code
        :param area_code: area code
        :param payload: UD area object"""
        return super().create(emp_code, self.subpath.path, area_code, payload=payload, **kwargs)

    def delete(self, emp_code: str, area_code: str, **kwargs):
        """Delete all data from a UD area for a given employee.
        :param emp_code: employee code
        :param area_code: area code"""
        return self._delete(emp_code, self.subpath.path, area_code)

    def get(self, emp_code: str, area_code: str, **kwargs):
        """Get a UD area for a employee.
        :param emp_code: employee code
        :param ud_area: area code"""
        return self._get(emp_code, self.subpath.path, area_code, **kwargs)

    def get_all(self, emp_code: str, **kwargs):
        """Get all UD areas for a given employee."""
        return self._get(emp_code, self.subpath.path, **kwargs)

    def modify(self, emp_code: str, area_code: str, *, payload: PayloadObject, **kwargs):
        """Modify (PUT) the UD area data for a given employee. Requires a full object, not a patch.
        :param emp_code: employee code
        :param area_code: area code
        :param payload: UD area object"""
        return self._put(emp_code, self.subpath.path, area_code, json=payload, **kwargs)

    def update(self, emp_code: str, area_code: str, *, payload: PayloadObject, **kwargs):
        """Update (PATCH) specific data in the UD area data for a given employee.
        :param emp_code: employee code
        :param area_code: area code
        :param payload: UD area object"""
        return self._patch(emp_code, self.subpath.path, area_code, data=payload, **kwargs)

    def download_attachment(
        self,
        emp_code: str,
        area_code: str,
        attach_id: str,
        *,
        dest: Optional[Path] = None,
        out_fn: Optional[str] = None,
        **kwargs
    ):
        """Download an attachment.
        :param emp_code: employee code
        :param area_code: area code
        :param attach_id: attachment code
        :param dest: optionally overried the default directory where content will be stored"""
        paths = (emp_code, self.subpath.path, area_code, self.subpath.attachments.path, attach_id)
        return super().download(*paths, dest=dest, out_fn=out_fn, **kwargs)

    def upload_attachment(
        self,
        emp_code: str,
        area_code: str,
        *,
        fp: Path,
        **kwargs
    ):
        """Download an attachment.
        :param emp_code: employee code
        :param area_code: area code
        :param fp: path object"""
        paths = (emp_code, self.subpath.path, area_code, self.subpath.attachments.path)
        return super().upload(*paths, fp=fp, **kwargs)


class Employees(EndpointBase):
    """Employees endpoint."""

    def __init__(self, session: APISession, *, endpoint: str = "employees") -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.confidential_notes: EmployeeNotes = EmployeeNotes(
            session, endpoint=self.endpoint, note_type="confidential"
        )
        self.standard_notes: EmployeeNotes = EmployeeNotes(session, endpoint=self.endpoint)
        self.photos: EmployeePhotos = EmployeePhotos(session, endpoint=self.endpoint)

        self.options: EmployeeOptions = EmployeeOptions(session, endpoint=self.endpoint)

    def get(self, emp_code, **kwargs):
        """Get an employee."""
        return self._get(emp_code, **kwargs)

    def get_all(self, **kwargs):
        """Get all employees."""
        return self.paginate(**kwargs)

    def modify(self, emp_code: str, *, payload: PayloadObject, **kwargs):
        """Modify (PUT) the employee record. Requires a full object, not a patch.
        :param emp_code: employee code
        :param payload: employee object"""
        return self._put(emp_code, json=payload, **kwargs)

    def update(self, emp_code: str, *, payload: PayloadObject, **kwargs):
        """Update (PATCH) the employee record.
        :param emp_code: employee code
        :param payload: employee object"""
        return self._patch(emp_code, data=payload, **kwargs)

    def get_current(self, doe: Optional[str] = None, dol: Optional[str] = None, **kwargs):
        """Convenience method for getting current employees. Note, the date of leaving ('dol') value in TASS is
        generally set to be the day after the employees actual last day; so if the employee's last day at school was the
        '2026-02-19' value, then the date of leaving should be entered in TASS as '2026-02-20'.
        OData filter uses 'ge' (greater than/equal to) for the date of leaving (or null), and 'le' (less than/equal to)
        for the date of entry.
        :param doe: optional date of entry string, for example '2026-01-01'
        :param dol: optional date of leaving string, for example '2026-12-31'"""
        doe = doe or self.today
        dol = dol or self.today
        date_fltr = f"doe le {doe} and (dol ge {dol} or dol eq null)"
        kwargs = self.merge_filter_param(date_fltr, kwargs=kwargs)

        return self.get_all(**kwargs)

    def get_future(self, doe: Optional[str] = None, **kwargs):
        """Convenience method for getting any future 'current' employees that have been migrated to 'current', but
        where their doe value does not yet make them current. The OData filter used is 'ge' (greater than/equal to)
        :param doe: optional date of entry string, for example '2026-01-01'"""
        doe = self.today
        date_fltr = f"doe ge {doe}"
        kwargs = self.merge_filter_param(date_fltr, kwargs=kwargs)

        return self.get_all(**kwargs)
