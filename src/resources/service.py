from src.generated.model import SrcAppEndpointsServiceGetServicesResponse
from src.http_client import AmigoHttpClient


class ServiceResource:
    """Service resource for Amigo API operations."""

    def __init__(
        self, http_client: AmigoHttpClient, organization_id: str
    ) -> SrcAppEndpointsServiceGetServicesResponse:
        self._http = http_client
        self._organization_id = organization_id

    # TODO: Add pagination
    async def get_services(self) -> SrcAppEndpointsServiceGetServicesResponse:
        """Get all services."""
        response = await self._http.request(
            "GET", f"/v1/{self._organization_id}/service/"
        )
        return SrcAppEndpointsServiceGetServicesResponse.model_validate_json(
            response.text
        )
