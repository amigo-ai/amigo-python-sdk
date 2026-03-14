from amigo_sdk.generated.model import (
    CreateAgentVersionParametersQuery,
    GetAgentsParametersQuery,
    GetAgentVersionsParametersQuery,
    OrganizationCreateAgentRequest,
    OrganizationCreateAgentResponse,
    OrganizationCreateAgentVersionRequest,
    OrganizationCreateAgentVersionResponse,
    OrganizationGetAgentsResponse,
    OrganizationGetAgentVersionsResponse,
)
from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient


class AsyncAgentResource:
    """Agent resource for Amigo API operations."""

    def __init__(self, http_client: AmigoAsyncHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    async def create_agent(
        self, body: OrganizationCreateAgentRequest
    ) -> OrganizationCreateAgentResponse:
        """Create a new agent in the organization."""
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/agent",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return OrganizationCreateAgentResponse.model_validate_json(response.text)

    async def get_agents(
        self, params: GetAgentsParametersQuery | None = None
    ) -> OrganizationGetAgentsResponse:
        """Get a list of agents in the organization."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/agent",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return OrganizationGetAgentsResponse.model_validate_json(response.text)

    async def delete_agent(self, agent_id: str) -> None:
        """Delete an agent by ID. Returns None on success (e.g., 204)."""
        await self._http.request(
            "DELETE",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/",
        )

    async def create_agent_version(
        self,
        agent_id: str,
        body: OrganizationCreateAgentVersionRequest,
        version: int | None = None,
    ) -> OrganizationCreateAgentVersionResponse:
        """Create a new version for an agent."""
        params = None
        if version is not None:
            query = CreateAgentVersionParametersQuery(version=version)
            params = query.model_dump(mode="json", exclude_none=True)
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/",
            json=body.model_dump(mode="json", exclude_none=True),
            params=params,
        )
        return OrganizationCreateAgentVersionResponse.model_validate_json(response.text)

    async def get_agent_versions(
        self, agent_id: str, params: GetAgentVersionsParametersQuery | None = None
    ) -> OrganizationGetAgentVersionsResponse:
        """Get versions for a specific agent."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/version",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return OrganizationGetAgentVersionsResponse.model_validate_json(response.text)

    # --- Convenience aliases ---

    async def list(
        self, params: GetAgentsParametersQuery | None = None
    ) -> OrganizationGetAgentsResponse:
        """Alias for get_agents."""
        return await self.get_agents(params)

    async def create(
        self, body: OrganizationCreateAgentRequest
    ) -> OrganizationCreateAgentResponse:
        """Alias for create_agent."""
        return await self.create_agent(body)

    async def delete(self, agent_id: str) -> None:
        """Alias for delete_agent."""
        return await self.delete_agent(agent_id)


class AgentResource:
    """Agent resource (synchronous)."""

    def __init__(self, http_client: AmigoHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    def create_agent(
        self, body: OrganizationCreateAgentRequest
    ) -> OrganizationCreateAgentResponse:
        """Create a new agent in the organization."""
        response = self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/agent",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return OrganizationCreateAgentResponse.model_validate_json(response.text)

    def get_agents(
        self, params: GetAgentsParametersQuery | None = None
    ) -> OrganizationGetAgentsResponse:
        """Get a list of agents in the organization."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/agent",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return OrganizationGetAgentsResponse.model_validate_json(response.text)

    def delete_agent(self, agent_id: str) -> None:
        """Delete an agent by ID."""
        self._http.request(
            "DELETE",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/",
        )

    def create_agent_version(
        self,
        agent_id: str,
        body: OrganizationCreateAgentVersionRequest,
        version: int | None = None,
    ) -> OrganizationCreateAgentVersionResponse:
        """Create a new version for an agent."""
        params = None
        if version is not None:
            query = CreateAgentVersionParametersQuery(version=version)
            params = query.model_dump(mode="json", exclude_none=True)
        response = self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/",
            json=body.model_dump(mode="json", exclude_none=True),
            params=params,
        )
        return OrganizationCreateAgentVersionResponse.model_validate_json(response.text)

    def get_agent_versions(
        self, agent_id: str, params: GetAgentVersionsParametersQuery | None = None
    ) -> OrganizationGetAgentVersionsResponse:
        """Get versions for a specific agent."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/agent/{agent_id}/version",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return OrganizationGetAgentVersionsResponse.model_validate_json(response.text)

    # --- Convenience aliases ---

    def list(
        self, params: GetAgentsParametersQuery | None = None
    ) -> OrganizationGetAgentsResponse:
        """Alias for get_agents."""
        return self.get_agents(params)

    def create(
        self, body: OrganizationCreateAgentRequest
    ) -> OrganizationCreateAgentResponse:
        """Alias for create_agent."""
        return self.create_agent(body)

    def delete(self, agent_id: str) -> None:
        """Alias for delete_agent."""
        return self.delete_agent(agent_id)
