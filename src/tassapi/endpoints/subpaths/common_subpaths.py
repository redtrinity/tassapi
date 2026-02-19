"""Common sub-path endpoints that are shared by various primary endpoints.

Define a class using the convention 'SubendpointNameSubPath', and then ensure
a 'path' string attribute is declared.

If a sub-path endpoint has additional sub-paths, then create an instance of the
'SubendpointNameSubPath' class inside the sub-path class.

If a sub-path endpoint has multiple "root" sub-path options (for example, 'Notes' have either
'confidential' or 'standard' sub-paths), the name should end in the 'SubPaths' suffix.

Examples:

class AttachmentsSubPath:
    path: str = "attachments"


class ConfidentialNotesSubPath:
    path: str = "notes/confidential"
    attachments: AttachmentsSubPath = AttachmentsSubPath
"""


class AttachmentsSubPath:
    path: str = "attachments"


class ConfidentialNotesSubPath:
    path: str = "notes/confidential"
    attachments: AttachmentsSubPath = AttachmentsSubPath


class StandardNotesSubPath:
    path: str = "notes/standard"
    attachments: AttachmentsSubPath = AttachmentsSubPath


class NotesSubPaths:
    confidential: ConfidentialNotesSubPath = ConfidentialNotesSubPath
    standard: StandardNotesSubPath = StandardNotesSubPath


class PhotoChangesSubPath:
    path: str = "changes"


class PhotosSubPath:
    path: str = "photo"
    changes: PhotoChangesSubPath = PhotoChangesSubPath


class UDAreasSubPath:
    path: str = "udareas"
    attachments: AttachmentsSubPath = AttachmentsSubPath


class UDFieldsSubPath:
    path: str = "udfields"
