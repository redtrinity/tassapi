from pathlib import Path
from typing import Optional

from .base import EndpointBase
from .options.students import StudentOptions
from .subpaths import NotesSubPaths, PhotosSubPath, UDAreasSubPath, UDFieldsSubPath
from .subpaths.students import StudentCommunicationRulesSubPath
from ..api.protocols import APISession
from ..utils.typehints import PayloadObject


class StudentCommunicationRules(EndpointBase):
    """Student communication rules endpoint."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = StudentCommunicationRulesSubPath

    def get_all(self, **kwargs):
        """Get all communication rules for all students."""
        return super().paginate(self.subpath.path, **kwargs)

    def get(self, stud_code: str, rule_type: Optional[str] = None, **kwargs):
        """Get communication rules for a specific student.
        :param stud_code: student code
        :param rule_type: optional string to get communication rules for a student by a specific type"""
        paths = (stud_code, self.subpath.path, rule_type)
        return self._get(*paths, **kwargs)


class StudentNotes(EndpointBase):
    """Student notes endpoint."""

    new_obj_keys = ("note_cat", "note_text", "note_date")

    def __init__(self, session: APISession, endpoint: str, note_type: Optional[str] = None) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = NotesSubPaths.confidential if note_type == "confidential" else NotesSubPaths.standard

    def create(self, stud_code: str, *, payload: PayloadObject, **kwargs):
        """Create an student note.
        :param stud_code: student code
        :param payload: note payload; required keys: 'note_cat', 'note_text', 'note_date'"""
        return super().create(stud_code, self.subpath.path, payload=payload, validate_keys=self.new_obj_keys, **kwargs)

    def get(self, stud_code: str, note_uid: str, **kwargs):
        """Get a note for an student.
        :param stud_code: student code
        :param note_uid: note uid"""
        return self._get(stud_code, self.subpath.path, note_uid, **kwargs)

    def get_all(self, stud_code: str, **kwargs):
        """Get all notes for a given student."""
        return self.paginate(stud_code, self.subpath.path, **kwargs)

    def get_attachments(self, stud_code: str, note_uid: str, **kwargs):
        """Get attachments for a given note. This does not download the attachment but returns attachment information
        such as file name, file size, date uploaded, and the 'attach_id' which is required to download an attachment.
        :param stud_code: student code
        :param note_uid: note uid"""
        return self._get(stud_code, self.subpath.path, note_uid, self.subpath.attachments.path, **kwargs)

    def download_attachment(
        self,
        stud_code: str,
        note_uid: str,
        attach_id: str,
        *,
        dest: Optional[Path] = None,
        out_fn: Optional[str] = None,
        **kwargs
    ):
        """Download an attachment.
        :param stud_code: student code
        :param note_uid: note uid
        :param attach_id: attachment code
        :param dest: optionally overried the default directory where content will be stored"""
        paths = (stud_code, self.subpath.path, note_uid, self.subpath.attachments.path, attach_id)
        return super().download(*paths, dest=dest, out_fn=out_fn, **kwargs)

    def upload_attachment(
        self,
        stud_code: str,
        note_uid: str,
        *,
        fp: Path,
        **kwargs
    ):
        """Upload an attachment.
        :param stud_code: student code
        :param note_uid: note uid
        :param fp: path object"""
        paths = (stud_code, self.subpath.path, note_uid, self.subpath.attachments.path)
        return super().upload(*paths, fp=fp, **kwargs)


class StudentPhotos(EndpointBase):
    """Student photos endpoint."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = PhotosSubPath

    def download_photos(self, stud_code: str, *, dest: Optional[Path] = None, out_fn: Optional[str] = None, **kwargs):
        """Downloads the ZIP file containing the photo and thumbnail."""
        return super().download(stud_code, self.subpath.path, dest=dest, out_fn=out_fn)

    def get_change_history(self, change_key: Optional[str] = None, **kwargs):
        """Get all the change history. If 'change_key' is not provided, then all changes are returned; if a value
        for 'change_key' is provided, then those specific changes are returned.

        To get valid values for 'change_key' this method must be called without a value provided.
        :param change_key: optional change key"""
        paths = (self.subpath.path, self.subpath.changes.path, change_key)
        return self._get(*paths, **kwargs)

    def upload_photo(
        self,
        stud_code: str,
        *,
        fp: Path,
        **kwargs
    ):
        """Upload a student photo.
        :param stud_code: student code
        :param fp: path object"""
        paths = (stud_code, self.subpath.path)
        return super().upload(*paths, fp=fp, **kwargs)


class StudentUDAreas(EndpointBase):
    """Student UD areas endpoint."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = UDAreasSubPath

    def create(self, stud_code: str, area_code: str, *, payload: PayloadObject, **kwargs):
        """Create data in a UD area object for a student. The specific UD area must already be configured in Student
        Setup.
        :param stud_code: student code
        :param area_code: area code
        :param payload: UD area object"""
        return super().create(stud_code, self.subpath.path, area_code, payload=payload, **kwargs)

    def delete(self, stud_code: str, area_code: str, **kwargs):
        """Delete all data from a UD area for a given student.
        :param stud_code: student code
        :param area_code: area code"""
        return self._delete(stud_code, self.subpath.path, area_code)

    def get(self, stud_code: str, area_code: str, **kwargs):
        """Get a UD area for a student.
        :param stud_code: student code
        :param ud_area: area code"""
        return self._get(stud_code, self.subpath.path, area_code, **kwargs)

    def get_all(self, stud_code: str, **kwargs):
        """Get all UD areas for a given student."""
        return self._get(stud_code, self.subpath.path, **kwargs)

    def modify(self, stud_code: str, area_code: str, *, payload: PayloadObject, **kwargs):
        """Modify (PUT) the UD area data for a given student. Requires a full object, not a patch.
        :param stud_code: student code
        :param area_code: area code
        :param payload: UD area object"""
        return self._put(stud_code, self.subpath.path, area_code, json=payload, **kwargs)

    def update(self, stud_code: str, area_code: str, *, payload: PayloadObject, **kwargs):
        """Update (PATCH) specific data in the UD area data for a given student.
        :param stud_code: student code
        :param area_code: area code
        :param payload: UD area object"""
        return self._patch(stud_code, self.subpath.path, area_code, data=payload, **kwargs)

    def download_attachment(
        self,
        stud_code: str,
        area_code: str,
        attach_id: str,
        *,
        dest: Optional[Path] = None,
        out_fn: Optional[str] = None,
        **kwargs
    ):
        """Download an attachment.
        :param stud_code: student code
        :param area_code: area code
        :param attach_id: attachment code
        :param dest: optionally overried the default directory where content will be stored"""
        paths = (stud_code, self.subpath.path, area_code, self.subpath.attachments.path, attach_id)
        return super().download(*paths, dest=dest, out_fn=out_fn, **kwargs)

    def upload_attachment(
        self,
        stud_code: str,
        area_code: str,
        *,
        fp: Path,
        **kwargs
    ):
        """Download an attachment.
        :param stud_code: student code
        :param area_code: area code
        :param fp: path object"""
        paths = (stud_code, self.subpath.path, area_code, self.subpath.attachments.path)
        return super().upload(*paths, fp=fp, **kwargs)


class StudentUDFields(EndpointBase):
    """Student UD fields endpoint."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = UDFieldsSubPath

    def get(self, stud_code: str, **kwargs):
        """Get a UD field for a student.
        :param stud_code: student code"""
        return self._get(stud_code, self.subpath.path, **kwargs)

    def modify(self, stud_code: str, *, payload: PayloadObject, **kwargs):
        """Modify (PUT) the UD field data for a given student. Requires a full object, not a patch.
        :param stud_code: student code
        :param payload: UD area object"""
        return self._put(stud_code, self.subpath.path, json=payload, **kwargs)

    def update(self, stud_code: str, area_code: str, *, payload: PayloadObject, **kwargs):
        """Update (PATCH) specific data in the UD field data for a given student.
        :param stud_code: student code
        :param area_code: area code
        :param payload: UD area object"""
        return self._patch(stud_code, self.subpath.path, area_code, data=payload, **kwargs)


class Students(EndpointBase):
    """Students endpoint."""

    def __init__(self, session: APISession, *, endpoint: str = "students") -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.communication_rules: StudentCommunicationRules = StudentCommunicationRules(session, endpoint=self.endpoint)
        self.confidential_notes: StudentNotes = StudentNotes(
            session, endpoint=self.endpoint, note_type="confidential"
        )
        self.standard_notes: StudentNotes = StudentNotes(session, endpoint=self.endpoint)
        self.photos: StudentPhotos = StudentPhotos(session, endpoint=self.endpoint)
        self.ud_areas: StudentUDAreas = StudentUDAreas(session, endpoint=self.endpoint)

        self.options: StudentOptions = StudentOptions(session)

    def get(self, stud_code, **kwargs):
        """Get an student."""
        return self._get(stud_code, **kwargs)

    def get_all(self, **kwargs):
        """Get all students."""
        return self.paginate(**kwargs)

    def modify(self, stud_code: str, *, payload: PayloadObject, **kwargs):
        """Modify (PUT) the student record. Requires a full object, not a patch.
        :param stud_code: student code
        :param payload: student object"""
        return self._put(stud_code, json=payload, **kwargs)

    def update(self, stud_code: str, *, payload: PayloadObject, **kwargs):
        """Update (PATCH) the student record.
        :param stud_code: student code
        :param payload: student object"""
        return self._patch(stud_code, data=payload, **kwargs)

    def get_current(self, doe: Optional[str] = None, dol: Optional[str] = None, **kwargs):
        """Convenience method for getting current students. Note, the date of leaving ('dol') value in TASS is
        generally set to be the day after the students actual last day; so if the student's last day at school was the
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
        """Convenience method for getting any future 'current' students that have been migrated to 'current', but
        where their doe value does not yet make them current. The OData filter used is 'ge' (greater than/equal to)
        :param doe: optional date of entry string, for example '2026-01-01'"""
        doe = self.today
        date_fltr = f"doe ge {doe}"
        kwargs = self.merge_filter_param(date_fltr, kwargs=kwargs)

        return self.get_all(**kwargs)
