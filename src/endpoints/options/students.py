from .common_options import (
    UDAreasOptions as StudentUDAreasOptions,
    UDFieldsOptions as StudentUDFieldsOptions,
)
from ..base import EndpointBase
from ..subpaths.students import StudentCommunicationRulesSubPath
from ...api.protocols import APISession


class StudentCommunicationRulesOptions(EndpointBase):
    """Student communication rules options endpoint."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = StudentCommunicationRulesSubPath

    def comm_rule_types(self):
        """Get communication rules types."""
        return self._get(self.subpath.path, "types")

    def genders(self):
        """Get genders."""
        return self._get(self.subpath.path, "genders")


class StudentNotesOptions(EndpointBase):
    """Student notes endpoint."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = "notes"  # options endpoint doesn't care about confidential/standard types

    def categories(self):
        """Get note categories. Values returned here are identical across confidential/standard note types."""
        return self._get(self.subpath, "categories")


class StudentOptions(EndpointBase):
    """Student options endpoint."""

    def __init__(self, session: APISession, *, endpoint: str = "options/students") -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.communication_rules: StudentCommunicationRulesOptions = StudentCommunicationRulesOptions(
            session, endpoint=self.endpoint
        )
        self.notes: StudentNotesOptions = StudentNotesOptions(session, endpoint=self.endpoint)
        self.ud_areas: StudentUDAreasOptions = StudentUDAreasOptions(session, endpoint=self.endpoint)
        self.ud_fields: StudentUDFieldsOptions = StudentUDFieldsOptions(session, endpoint=self.endpoint)

    def campuses(self):
        """Get campus options."""
        return self._get("campuses")

    def comparative_reporting_types(self):
        """Get comparative reporting types."""
        return self._get("comparativereportingtypes")

    def feeder_schools(self):
        """Get feeder schools."""
        return self._get("feederschools")

    def houses(self):
        """Get houses."""
        return self._get("houses")

    def next_year_indicators(self):
        """Get next year indicators."""
        return self._get("nextyearindicators")

    def pc_tutor_groups(self):
        """Get PC/Tutor Groups."""
        return self._get("pctutorgroups")

    def religions(self):
        """Get religions."""
        return self._get("religions")

    def residency_statuses(self):
        """Get residency statuses."""
        return self._get("residencystatuses")

    def year_groups(self):
        """Get year groups."""
        return self._get("yeargroups")
