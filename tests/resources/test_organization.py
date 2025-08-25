from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from amigo_sdk.config import AmigoConfig
from amigo_sdk.errors import NotFoundError
from amigo_sdk.generated.model import (
    OrganizationGetOrganizationResponse,
)
from amigo_sdk.http_client import AmigoAsyncHttpClient
from amigo_sdk.resources.organization import AsyncOrganizationResource

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
def organization_resource(mock_config) -> AsyncOrganizationResource:
    http_client = AmigoAsyncHttpClient(mock_config)
    return AsyncOrganizationResource(http_client, "test-org-123")


@pytest.fixture(autouse=True)
def _mock_signin_token():
    fresh_token = Mock(
        id_token="tok",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    with patch(
        "amigo_sdk.http_client.sign_in_with_api_key_async", return_value=fresh_token
    ):
        yield


@pytest.mark.unit
class TestOrganizationResource:
    """Simple test suite for the Organization Resource."""

    @pytest.mark.asyncio
    async def test_get_organization_returns_expected_data(
        self, organization_resource: AsyncOrganizationResource
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
        self, organization_resource: AsyncOrganizationResource
    ) -> None:
        """Test get method raises NotFoundError for non-existent organization."""
        async with mock_http_request(
            '{"error": "Organization not found"}', status_code=404
        ):
            with pytest.raises(NotFoundError):
                await organization_resource.get()
