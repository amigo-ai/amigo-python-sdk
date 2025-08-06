import pytest

from src.config import AmigoConfig
from src.http_client import AmigoHttpClient
from src.resources.service import ServiceResource
from src.errors import NotFoundError
from src.generated.model import SrcAppEndpointsServiceGetServicesResponse

from .helpers import mock_http_request, create_services_response_data


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
    http_client = AmigoHttpClient(mock_config)
    return ServiceResource(http_client, "test-org-123")


@pytest.mark.unit
class TestServiceResource:
    """Simple test suite for ServiceResource."""

    @pytest.mark.asyncio
    async def test_get_services_returns_expected_data(self, service_resource):
        """Test get_services method returns properly parsed services data."""
        mock_data = create_services_response_data()

        async with mock_http_request(mock_data):
            result = await service_resource.get_services()

            assert isinstance(result, SrcAppEndpointsServiceGetServicesResponse)
            assert len(result.services) == 2
            assert result.services[0].id == "service-1"
            assert result.services[0].name == "Customer Support Bot"
            assert result.services[1].id == "service-2"
            assert result.has_more == False
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
