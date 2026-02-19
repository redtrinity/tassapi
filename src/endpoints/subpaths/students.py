"""Student endpoint specific sub-paths.

Define a class using the convention 'SubendpointNameSubPath', and then ensure
a 'path' string attribute is declared.
If a sub-path endpoint has additional sub-paths, then create an instance of the
'SubendpointNameSubPath' class inside the sub-path class.

Examples:

class AttachmentsSubPath:
    path: str = "attachments"


class ConfidentialNotesSubPath:
    path: str = "notes/confidential"
    attachments: AttachmentsSubPath = AttachmentsSubPath
"""


class StudentCommunicationRulesSubPath:
    path: str = "communicationrules"


class StudentMceecdyaSubPath:
    path: str = "mceecdya"
