import pytest

from src.config import AmigoConfig
from src.errors import NotFoundError
from src.generated.model import OrganizationGetOrganizationResponse
from src.http_client import AmigoHttpClient
from src.resources.organization import OrganizationResource

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
def organization_resource(mock_config):
    http_client = AmigoHttpClient(mock_config)
    return OrganizationResource(http_client, "test-org-123")


@pytest.mark.unit
class TestOrganizationResource:
    """Simple test suite for OrganizationResource."""

    @pytest.mark.asyncio
    async def test_get_organization_returns_expected_data(self, organization_resource):
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
        self, organization_resource
    ):
        """Test get method raises NotFoundError for non-existent organization."""
        async with mock_http_request(
            '{"error": "Organization not found"}', status_code=404
        ):
            with pytest.raises(NotFoundError):
                await organization_resource.get()
