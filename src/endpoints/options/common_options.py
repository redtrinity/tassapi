from ..base import EndpointBase
from ...api.protocols import APISession


class UDAreasOptions(EndpointBase):
    """UD area options; this is an endpoint path shared by various primary endpoints like students, employees,
    so only basic class setup is provided here. This class should be inherited by other classes that implemment
    UD area endpoints."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = "udareas"  # common path

    def get(self, area_code: str, **kwargs):
        """Get the setup for a specific UD area.
        :param area_code: area code"""
        return self._get(self.subpath, area_code, **kwargs)

    def get_all(self, **kwargs):
        """Get the setup data for all UD areas."""
        return self._get(self.subpath, **kwargs)


class UDFieldsOptions(EndpointBase):
    """UD field options; this is an endpoint path shared by various primary endpoints like students, employees,
    so only basic class setup is provided here. This class should be inherited by other classes that implemment
    UD area endpoints."""

    def __init__(self, session: APISession, endpoint: str) -> None:
        super().__init__(session)
        self.endpoint = endpoint
        self.subpath = "udfields"  # common path

    def get(self, **kwargs):
        """Get the setup data for all UD fields."""
        return self._get(self.subpath, **kwargs)

    def get_all(self, **kwargs):
        """Aliases 'UDFieldsOptions.get' as there aren't specific 'areas' to get option data for."""
        return self.get(**kwargs)
