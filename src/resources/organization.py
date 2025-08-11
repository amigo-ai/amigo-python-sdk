from typing import Optional

from src.generated.model import (
    CreateAgentVersionParametersQuery,
    GetAgentsParametersQuery,
    GetAgentVersionsParametersQuery,
    OrganizationCreateAgentRequest,
    OrganizationCreateAgentResponse,
    OrganizationCreateAgentVersionRequest,
    OrganizationCreateAgentVersionResponse,
    OrganizationGetAgentsResponse,
    OrganizationGetAgentVersionsResponse,
    OrganizationGetOrganizationResponse,
)
from src.http_client import AmigoHttpClient


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

    async def create_agent(
        self, body: OrganizationCreateAgentRequest
    ) -> OrganizationCreateAgentResponse:
        """
        Create an agent for an organization.
        """
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/agent",
            json=body.model_dump(),
        )

        return OrganizationCreateAgentResponse.model_validate_json(response.text)

    async def create_agent_version(
        self,
        agent_id: str,
        body: OrganizationCreateAgentVersionRequest,
        params: Optional[CreateAgentVersionParametersQuery] = None,
    ) -> OrganizationCreateAgentVersionResponse:
        """
        Create a version of an agent.
        """
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/",
            json=body.model_dump(),
            params=params.model_dump() if params else None,
        )

        return OrganizationCreateAgentVersionResponse.model_validate_json(response.text)

    async def get_agents(
        self, params: GetAgentsParametersQuery
    ) -> OrganizationGetAgentsResponse:
        """
        Return list of agents for an organization.
        """
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/agent",
            params=params.model_dump(),
        )

        return OrganizationGetAgentsResponse.model_validate_json(response.text)

    async def delete_agent(self, agent_id: str) -> None:
        """
        Delete an agent for an organization.
        """
        await self._http.request(
            "DELETE",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/",
        )

    async def get_agent_versions(
        self, agent_id: str, params: GetAgentVersionsParametersQuery
    ) -> OrganizationGetAgentVersionsResponse:
        """
        Return list of versions for an agent.
        """
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/version",
            params=params.model_dump(),
        )

        return OrganizationGetAgentVersionsResponse.model_validate_json(response.text)
