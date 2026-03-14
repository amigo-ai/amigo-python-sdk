import pytest

from amigo_sdk.config import AmigoConfig
from amigo_sdk.errors import NotFoundError
from amigo_sdk.generated.model import ServiceGetServicesResponse
from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient
from amigo_sdk.resources.service import AsyncServiceResource, ServiceResource

from .helpers import (
    create_services_response_data,
    mock_http_request,
    mock_http_request_sync,
)


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
def service_resource(mock_config):
    http_client = AmigoAsyncHttpClient(mock_config)
    return AsyncServiceResource(http_client, "test-org-123")


@pytest.mark.unit
class TestServiceResource:
    """Simple test suite for ServiceResource."""

    @pytest.mark.asyncio
    async def test_get_services_returns_expected_data(self, service_resource):
        """Test get_services method returns properly parsed services data."""
        mock_data = create_services_response_data()

        async with mock_http_request(mock_data):
            result = await service_resource.get_services()

            assert isinstance(result, ServiceGetServicesResponse)
            assert len(result.services) == 2
            assert result.services[0].id == "service-1"
            assert result.services[0].name == "Customer Support Bot"
            assert result.services[1].id == "service-2"
            assert not result.has_more
            assert result.continuation_token is None

    @pytest.mark.asyncio
    async def test_get_services_nonexistent_organization_raises_not_found(
        self, service_resource
    ):
        """Test get_services method raises NotFoundError for non-existent organization."""
        async with mock_http_request(
            '{"error": "Organization not found"}', status_code=404
        ):
            with pytest.raises(NotFoundError):
                await service_resource.get_services()

    @pytest.mark.asyncio
    async def test_create_service(self, service_resource):
        from amigo_sdk.generated.model import ServiceCreateServiceRequest

        mock_data = {"id": "svc-async-1"}
        body = ServiceCreateServiceRequest(
            name="test-svc",
            description="desc",
            keyterms=[],
            tags={},
            is_active=False,
            agent_id="aaaaaaaaaaaaaaaaaaaaaaaa",
            service_hierarchical_state_machine_id="bbbbbbbbbbbbbbbbbbbbbbbb",
        )
        async with mock_http_request(mock_data):
            result = await service_resource.create_service(body)
            assert result.id == "svc-async-1"

    @pytest.mark.asyncio
    async def test_update_service(self, service_resource):
        from amigo_sdk.generated.model import ServiceUpdateServiceRequest

        body = ServiceUpdateServiceRequest(is_active=True)
        async with mock_http_request("", status_code=204):
            await service_resource.update_service("svc-1", body)

    @pytest.mark.asyncio
    async def test_delete_version_set(self, service_resource):
        async with mock_http_request("", status_code=204):
            await service_resource.delete_version_set("svc-1", "staging")

    @pytest.mark.asyncio
    async def test_list_alias(self, service_resource):
        mock_data = create_services_response_data()
        async with mock_http_request(mock_data):
            result = await service_resource.list()
            assert isinstance(result, ServiceGetServicesResponse)

    @pytest.mark.asyncio
    async def test_create_alias(self, service_resource):
        from amigo_sdk.generated.model import ServiceCreateServiceRequest

        mock_data = {"id": "svc-alias-1"}
        body = ServiceCreateServiceRequest(
            name="test-svc",
            description="desc",
            keyterms=[],
            tags={},
            is_active=False,
            agent_id="aaaaaaaaaaaaaaaaaaaaaaaa",
            service_hierarchical_state_machine_id="bbbbbbbbbbbbbbbbbbbbbbbb",
        )
        async with mock_http_request(mock_data):
            result = await service_resource.create(body)
            assert result.id == "svc-alias-1"


@pytest.mark.unit
class TestServiceResourceSync:
    """Sync ServiceResource tests mirroring async coverage."""

    def _resource(self, mock_config) -> ServiceResource:
        http = AmigoHttpClient(mock_config)
        return ServiceResource(http, mock_config.organization_id)

    def test_get_services_returns_expected_data_sync(self, mock_config):
        res = self._resource(mock_config)
        mock_data = create_services_response_data()
        with mock_http_request_sync(mock_data):
            result = res.get_services()
            assert isinstance(result, ServiceGetServicesResponse)
            assert len(result.services) == 2
            assert result.services[0].id == "service-1"

    def test_get_services_nonexistent_organization_raises_not_found_sync(
        self, mock_config
    ):
        res = self._resource(mock_config)
        with mock_http_request_sync(
            '{"error": "Organization not found"}', status_code=404
        ):
            with pytest.raises(NotFoundError):
                res.get_services()

    def test_create_service_sync(self, mock_config):
        from amigo_sdk.generated.model import ServiceCreateServiceRequest

        res = self._resource(mock_config)
        mock_data = {"id": "svc-123"}
        body = ServiceCreateServiceRequest(
            name="test-svc",
            description="A test service",
            keyterms=[],
            tags={},
            is_active=False,
            agent_id="aaaaaaaaaaaaaaaaaaaaaaaa",
            service_hierarchical_state_machine_id="bbbbbbbbbbbbbbbbbbbbbbbb",
        )
        with mock_http_request_sync(mock_data):
            result = res.create_service(body)
            assert result.id == "svc-123"

    def test_update_service_sync(self, mock_config):
        from amigo_sdk.generated.model import ServiceUpdateServiceRequest

        res = self._resource(mock_config)
        body = ServiceUpdateServiceRequest(is_active=True)
        with mock_http_request_sync("", status_code=204):
            res.update_service("svc-123", body)

    def test_delete_version_set_sync(self, mock_config):
        res = self._resource(mock_config)
        with mock_http_request_sync("", status_code=204):
            res.delete_version_set("svc-123", "staging")

    def test_list_alias_sync(self, mock_config):
        res = self._resource(mock_config)
        mock_data = create_services_response_data()
        with mock_http_request_sync(mock_data):
            result = res.list()
            assert isinstance(result, ServiceGetServicesResponse)
