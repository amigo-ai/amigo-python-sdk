from amigo_sdk.generated.model import (
    GetAgentsParametersQuery,
    GetAgentVersionsParametersQuery,
    OrganizationGetAgentsResponse,
    OrganizationGetAgentVersionsResponse,
    OrganizationGetOrganizationResponse,
)
from amigo_sdk.http_client import AmigoHttpClient


class OrganizationResource:
    """Organization resource for Amigo API operations."""

    def __init__(self, http_client: AmigoHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    async def get(self) -> OrganizationGetOrganizationResponse:
        """
        Get the details of an organization.
        """
        response = await self._http.request(
            "GET", f"/v1/{self._organization_id}/organization/"
        )

        return OrganizationGetOrganizationResponse.model_validate_json(response.text)

    async def get_agents(
        self, params: GetAgentsParametersQuery
    ) -> OrganizationGetAgentsResponse:
        """
        Return list of agents for an organization.
        """
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/agent",
            params=params.model_dump(mode="json", exclude_none=True),
        )

        return OrganizationGetAgentsResponse.model_validate_json(response.text)

    async def get_agent_versions(
        self, agent_id: str, params: GetAgentVersionsParametersQuery
    ) -> OrganizationGetAgentVersionsResponse:
        """
        Return list of versions for an agent.
        """
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/version",
            params=params.model_dump(mode="json", exclude_none=True),
        )

        return OrganizationGetAgentVersionsResponse.model_validate_json(response.text)
