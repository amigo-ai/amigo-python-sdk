import pytest
from datetime import datetime, timedelta

from src.auth import sign_in_with_api_key
from src.config import AmigoConfig
from src.errors import AuthenticationError
from src.generated.model import SrcAppEndpointsUserSignInWithApiKeyResponse


# Mock config for testing
@pytest.fixture
def mock_config():
    return AmigoConfig(
        api_key="test-api-key",
        api_key_id="test-api-key-id",
        user_id="test-user-id",
        organization_id="test-org-id",
        base_url="https://api.example.com",
    )


# Mock successful auth response
@pytest.fixture
def mock_success_response() -> SrcAppEndpointsUserSignInWithApiKeyResponse:
    expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
    return {"id_token": "mock-bearer-token-123", "expires_at": expires_at}


@pytest.mark.unit
class TestAuth:
    """Test suite for authentication functionality."""

    @pytest.mark.asyncio
    async def test_signin_request_has_correct_headers_and_url(
        self, mock_config, mock_success_response, httpx_mock
    ):
        """Test that outgoing signin_with_api_key request has correct headers and URL."""
        expected_url = "https://api.example.com/v1/test-org-id/user/signin_with_api_key"

        httpx_mock.add_response(
            method="POST", url=expected_url, json=mock_success_response, status_code=200
        )

        # Make the request
        await sign_in_with_api_key(mock_config)

        # Verify the request was made correctly
        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert str(request.url) == expected_url

        # Verify headers
        assert request.headers["x-api-key"] == "test-api-key"
        assert request.headers["x-api-key-id"] == "test-api-key-id"
        assert request.headers["x-user-id"] == "test-user-id"

    @pytest.mark.asyncio
    async def test_non_ok_response_throws_authentication_error(
        self, mock_config, httpx_mock
    ):
        """Test that non-OK response throws AuthenticationError."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/v1/test-org-id/user/signin_with_api_key",
            status_code=401,
            text="API key not found, is incorrect, or the requested user is not found.",
        )

        with pytest.raises(AuthenticationError):
            await sign_in_with_api_key(mock_config)

    @pytest.mark.asyncio
    async def test_response_json_is_parsed_correctly(
        self, mock_config, mock_success_response, httpx_mock
    ):
        """Test that response JSON is parsed into correct response type."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/v1/test-org-id/user/signin_with_api_key",
            json=mock_success_response,
            status_code=200,
        )

        response = await sign_in_with_api_key(mock_config)

        # Verify response structure
        assert response.id_token == "mock-bearer-token-123"
        # The model automatically parses the ISO string to datetime
        assert response.expires_at.isoformat() == mock_success_response["expires_at"]

    @pytest.mark.asyncio
    async def test_invalid_json_response_throws_authentication_error(
        self, mock_config, httpx_mock
    ):
        """Test that invalid JSON response throws AuthenticationError."""
        httpx_mock.add_response(
            method="POST",
            url="https://api.example.com/v1/test-org-id/user/signin_with_api_key",
            text="invalid json response",
            status_code=200,
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await sign_in_with_api_key(mock_config)

        assert "Invalid response format" in str(exc_info.value)
