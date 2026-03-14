import pytest

from amigo_sdk.config import AmigoConfig
from amigo_sdk.errors import NotFoundError
from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient
from amigo_sdk.resources.agent import AgentResource, AsyncAgentResource

from .helpers import mock_http_request, mock_http_request_sync


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
def agent_resource(mock_config) -> AsyncAgentResource:
    http_client = AmigoAsyncHttpClient(mock_config)
    return AsyncAgentResource(http_client, "test-org-123")


@pytest.mark.unit
class TestAgentResource:
    @pytest.mark.asyncio
    async def test_get_agents_returns_data(self, agent_resource):
        mock_data = {"agents": [], "has_more": False, "continuation_token": None}
        async with mock_http_request(mock_data):
            result = await agent_resource.get_agents()
            assert result.has_more is False

    @pytest.mark.asyncio
    async def test_create_agent_returns_id(self, agent_resource):
        from amigo_sdk.generated.model import OrganizationCreateAgentRequest

        mock_data = {"id": "agent-123"}
        body = OrganizationCreateAgentRequest(agent_name="test-agent")
        async with mock_http_request(mock_data):
            result = await agent_resource.create_agent(body)
            assert result.id == "agent-123"

    @pytest.mark.asyncio
    async def test_delete_agent_returns_none(self, agent_resource):
        async with mock_http_request("", status_code=204):
            await agent_resource.delete_agent("agent-123")

    @pytest.mark.asyncio
    async def test_get_agents_404_raises(self, agent_resource):
        async with mock_http_request('{"detail": "not found"}', status_code=404):
            with pytest.raises(NotFoundError):
                await agent_resource.get_agents()

    @pytest.mark.asyncio
    async def test_list_alias(self, agent_resource):
        mock_data = {"agents": [], "has_more": False, "continuation_token": None}
        async with mock_http_request(mock_data):
            result = await agent_resource.list()
            assert result.has_more is False


@pytest.mark.unit
class TestAgentResourceSync:
    def _resource(self, mock_config) -> AgentResource:
        http = AmigoHttpClient(mock_config)
        return AgentResource(http, mock_config.organization_id)

    def test_get_agents_returns_data_sync(self, mock_config):
        res = self._resource(mock_config)
        mock_data = {"agents": [], "has_more": False, "continuation_token": None}
        with mock_http_request_sync(mock_data):
            result = res.get_agents()
            assert result.has_more is False

    def test_create_agent_returns_id_sync(self, mock_config):
        from amigo_sdk.generated.model import OrganizationCreateAgentRequest

        res = self._resource(mock_config)
        mock_data = {"id": "agent-456"}
        body = OrganizationCreateAgentRequest(agent_name="test-agent")
        with mock_http_request_sync(mock_data):
            result = res.create_agent(body)
            assert result.id == "agent-456"

    def test_delete_agent_sync(self, mock_config):
        res = self._resource(mock_config)
        with mock_http_request_sync("", status_code=204):
            res.delete_agent("agent-123")
