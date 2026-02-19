from .common_options import UDAreasOptions as EmployeeUDAreasOptions
from ..base import EndpointBase
from ...api.protocols import APISession


class EmployeeNotesOptions(EndpointBase):
    """Employee notes endpoint."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = "notes"  # options endpoint doesn't care about confidential/standard types

    def categories(self):
        """Get note categories. Values returned here are identical across confidential/standard note types."""
        return self._get(self.subpath, "categories")


class EmployeeOptions(EndpointBase):
    """Employee options endpoint."""

    def __init__(self, session: APISession, *, endpoint: str = "options/employees") -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.notes: EmployeeNotesOptions = EmployeeNotesOptions(session, endpoint=self.endpoint)
        self.ud_areas: EmployeeUDAreasOptions = EmployeeUDAreasOptions(session, endpoint=self.endpoint)

    def countries(self):
        """Get country options."""
        return self._get("countries")

    def employee_statuses(self):
        """Get employee status types."""
        return self._get("statuses")

    def genders(self):
        """Get employee genders."""
        return self._get("genders")

    def indigenous_types(self):
        """Get indigenous types."""
        return self._get("indigenoustypes")

    def main_activities(self):
        """Get employee main activity types."""
        return self._get("mainactivities")

    def marital_statuses(self):
        """Get marital statuses."""
        return self._get("maritalstatuses")

    def termination_reasons(self):
        """Get termination reasons."""
        return self._get("terminationreasons")

    def titles(self):
        """Get employee title prefixes (honorifics)."""
        return self._get("titles")

    def vendors(self):
        """Get vendors."""
        return self._get("vendors")
