from src.generated.model import SrcAppEndpointsOrganizationGetOrganizationResponse
from src.http_client import AmigoHttpClient


class OrganizationResource:
    """Organization resource for Amigo API operations."""

    def __init__(self, http_client: AmigoHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    async def get(self) -> SrcAppEndpointsOrganizationGetOrganizationResponse:
        """
        Get the details of an organization.
        """
        # Make the API request
        response = await self._http.request(
            "GET", f"/v1/{self._organization_id}/organization/"
        )

        # Parse response as pydantic model
        return SrcAppEndpointsOrganizationGetOrganizationResponse.model_validate_json(
            response.text
        )
