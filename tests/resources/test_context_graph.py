import pytest

from amigo_sdk.config import AmigoConfig
from amigo_sdk.errors import NotFoundError
from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient
from amigo_sdk.resources.context_graph import (
    AsyncContextGraphResource,
    ContextGraphResource,
)

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
def cg_resource(mock_config) -> AsyncContextGraphResource:
    http_client = AmigoAsyncHttpClient(mock_config)
    return AsyncContextGraphResource(http_client, "test-org-123")


@pytest.mark.unit
class TestContextGraphResource:
    @pytest.mark.asyncio
    async def test_get_context_graphs_returns_data(self, cg_resource):
        mock_data = {
            "service_hierarchical_state_machines": [],
            "has_more": False,
            "continuation_token": None,
        }
        async with mock_http_request(mock_data):
            result = await cg_resource.get_context_graphs()
            assert result.has_more is False

    @pytest.mark.asyncio
    async def test_create_context_graph_returns_id(self, cg_resource):
        from amigo_sdk.generated.model import (
            OrganizationCreateServiceHierarchicalStateMachineRequest,
        )

        mock_data = {"id": "hsm-123"}
        body = OrganizationCreateServiceHierarchicalStateMachineRequest(
            state_machine_name="test-hsm"
        )
        async with mock_http_request(mock_data):
            result = await cg_resource.create_context_graph(body)
            assert result.id == "hsm-123"

    @pytest.mark.asyncio
    async def test_delete_context_graph_returns_none(self, cg_resource):
        async with mock_http_request("", status_code=204):
            await cg_resource.delete_context_graph("hsm-123")

    @pytest.mark.asyncio
    async def test_get_context_graphs_404_raises(self, cg_resource):
        async with mock_http_request('{"detail": "not found"}', status_code=404):
            with pytest.raises(NotFoundError):
                await cg_resource.get_context_graphs()

    @pytest.mark.asyncio
    async def test_list_alias(self, cg_resource):
        mock_data = {
            "service_hierarchical_state_machines": [],
            "has_more": False,
            "continuation_token": None,
        }
        async with mock_http_request(mock_data):
            result = await cg_resource.list()
            assert result.has_more is False


@pytest.mark.unit
class TestContextGraphResourceSync:
    def _resource(self, mock_config) -> ContextGraphResource:
        http = AmigoHttpClient(mock_config)
        return ContextGraphResource(http, mock_config.organization_id)

    def test_get_context_graphs_sync(self, mock_config):
        res = self._resource(mock_config)
        mock_data = {
            "service_hierarchical_state_machines": [],
            "has_more": False,
            "continuation_token": None,
        }
        with mock_http_request_sync(mock_data):
            result = res.get_context_graphs()
            assert result.has_more is False

    def test_delete_context_graph_sync(self, mock_config):
        res = self._resource(mock_config)
        with mock_http_request_sync("", status_code=204):
            res.delete_context_graph("hsm-123")
