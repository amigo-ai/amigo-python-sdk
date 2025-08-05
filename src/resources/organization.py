from typing import Optional
from src.generated.model import SrcAppEndpointsOrganizationGetOrganizationResponse
from src.http_client import AmigoHttpClient


class OrganizationResource:
    """Organization resource for Amigo API operations."""

    def __init__(self, http_client: AmigoHttpClient) -> None:
        self._http = http_client

    async def get(
        self, organization_id: Optional[str] = None
    ) -> SrcAppEndpointsOrganizationGetOrganizationResponse:
        """
        Get organization details.

        Args:
            organization_id: Organization ID to fetch.

        Returns:
            Organization data in JSON format.
        """
        # Use provided organization_id or fall back to client config
        org_id = organization_id or self._http._cfg.organization_id

        # Make the API request
        response = await self._http.request("GET", f"/v1/{org_id}/organization/")

        # Parse response as pydantic model
        return SrcAppEndpointsOrganizationGetOrganizationResponse.model_validate_json(
            response.text
        )
