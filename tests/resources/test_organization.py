import pytest

from amigo_sdk.config import AmigoConfig
from amigo_sdk.errors import NotFoundError
from amigo_sdk.generated.model import (
    GetAgentsParametersQuery,
    GetAgentVersionsParametersQuery,
    OrganizationGetAgentsResponse,
    OrganizationGetAgentsResponseAgentInstance,
    OrganizationGetAgentVersionsResponse,
    OrganizationGetOrganizationResponse,
)
from amigo_sdk.http_client import AmigoHttpClient
from amigo_sdk.resources.organization import OrganizationResource

from .helpers import create_organization_response_data, mock_http_request


@pytest.fixture
def mock_config():
    return AmigoConfig(
        api_key="test-api-key",
        api_key_id="test-api-key-id",
        user_id="test-user-id",
        organization_id="test-org-123",
        base_url="https://api.example.com",
    )


@pytest.fixture
def organization_resource(mock_config) -> OrganizationResource:
    http_client = AmigoHttpClient(mock_config)
    return OrganizationResource(http_client, "test-org-123")


@pytest.mark.unit
class TestOrganizationResource:
    """Simple test suite for the Organization Resource."""

    @pytest.mark.asyncio
    async def test_get_organization_returns_expected_data(
        self, organization_resource: OrganizationResource
    ):
        """Test get method returns properly parsed organization data."""
        mock_data = create_organization_response_data()

        async with mock_http_request(mock_data):
            result = await organization_resource.get()

            assert isinstance(result, OrganizationGetOrganizationResponse)
            assert result.org_id == "test-org-123"
            assert result.org_name == "Test Organization"
            assert result.title == "Your AI Assistant Platform"
            assert len(result.onboarding_instructions) == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_organization_raises_not_found(
        self, organization_resource: OrganizationResource
    ) -> None:
        """Test get method raises NotFoundError for non-existent organization."""
        async with mock_http_request(
            '{"error": "Organization not found"}', status_code=404
        ):
            with pytest.raises(NotFoundError):
                await organization_resource.get()

    # --- Get agents ---
    @pytest.mark.asyncio
    async def test_get_agents_happy_path(
        self, organization_resource: OrganizationResource
    ) -> None:
        params = GetAgentsParametersQuery()

        mock_response = OrganizationGetAgentsResponse(
            agents=[
                OrganizationGetAgentsResponseAgentInstance(
                    id="agent-1", name="Agent One", deprecated=False, latest_version=1
                )
            ],
            has_more=False,
            continuation_token=None,
        )

        async with mock_http_request(mock_response):
            result = await organization_resource.get_agents(params=params)

            assert isinstance(result, OrganizationGetAgentsResponse)
            assert len(result.agents) == 1
            assert result.agents[0].id == "agent-1"
            assert result.agents[0].name == "Agent One"

    @pytest.mark.asyncio
    async def test_get_agents_invalid_query_param_422(
        self, organization_resource: OrganizationResource
    ) -> None:
        from amigo_sdk.errors import ValidationError as SDKValidationError

        params = GetAgentsParametersQuery()

        async with mock_http_request('{"detail": "invalid query"}', status_code=422):
            with pytest.raises(SDKValidationError):
                await organization_resource.get_agents(params=params)

    @pytest.mark.asyncio
    async def test_get_agent_versions_happy_path(
        self, organization_resource: OrganizationResource
    ) -> None:
        params = GetAgentVersionsParametersQuery()

        mock_response = OrganizationGetAgentVersionsResponse(
            agent_versions=[], has_more=False, continuation_token=None
        )

        async with mock_http_request(mock_response):
            result = await organization_resource.get_agent_versions(
                agent_id="agent-1", params=params
            )

            assert isinstance(result, OrganizationGetAgentVersionsResponse)
            assert result.agent_versions == []

    @pytest.mark.asyncio
    async def test_get_agent_versions_non_2xx_raises_error(
        self, organization_resource: OrganizationResource
    ) -> None:
        params = GetAgentVersionsParametersQuery()

        async with mock_http_request('{"error": "Agent not found"}', status_code=404):
            with pytest.raises(NotFoundError):
                await organization_resource.get_agent_versions(
                    agent_id="missing-agent", params=params
                )
