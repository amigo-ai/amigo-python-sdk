from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from src.config import AmigoConfig
from src.errors import AuthenticationError, BadRequestError, NotFoundError
from src.http_client import AmigoHttpClient
from tests.resources.helpers import (
    mock_http_stream,
    mock_http_stream_sequence,
)


@pytest.fixture
def mock_config():
    return AmigoConfig(
        api_key="test-api-key",
        api_key_id="test-api-key-id",
        user_id="test-user-id",
        organization_id="test-org-id",
        base_url="https://api.example.com",
    )


@pytest.fixture
def mock_token_response():
    return Mock(
        id_token="test-bearer-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


@pytest.mark.unit
class TestAmigoHttpClient:
    """Test suite for AmigoHttpClient."""

    def test_client_initialization(self, mock_config):
        """Test client initializes correctly with config."""
        client = AmigoHttpClient(mock_config, timeout=30)
        assert client._cfg == mock_config
        assert client._token is None
        assert client._client.base_url == "https://api.example.com"

    @pytest.mark.asyncio
    async def test_ensure_token_fetches_new_token(
        self, mock_config, mock_token_response
    ):
        """Test _ensure_token fetches new token when none exists."""
        client = AmigoHttpClient(mock_config)

        with patch(
            "src.http_client.sign_in_with_api_key", return_value=mock_token_response
        ):
            token = await client._ensure_token()

        assert token == "test-bearer-token"
        assert client._token == mock_token_response

    @pytest.mark.asyncio
    async def test_ensure_token_refreshes_expired_token(self, mock_config):
        """Test _ensure_token refreshes token when expired."""
        client = AmigoHttpClient(mock_config)

        # Set an expired token (timezone-aware)
        expired_token = Mock(
            id_token="expired-token",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),  # Expired
        )
        client._token = expired_token

        fresh_token = Mock(
            id_token="fresh-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        with patch("src.http_client.sign_in_with_api_key", return_value=fresh_token):
            token = await client._ensure_token()

        assert token == "fresh-token"
        assert client._token == fresh_token

    @pytest.mark.asyncio
    async def test_ensure_token_handles_auth_failure(self, mock_config):
        """Test _ensure_token raises AuthenticationError when auth fails."""
        client = AmigoHttpClient(mock_config)

        with patch(
            "src.http_client.sign_in_with_api_key", side_effect=Exception("Auth failed")
        ):
            with pytest.raises(AuthenticationError):
                await client._ensure_token()

    @pytest.mark.asyncio
    async def test_request_adds_authorization_header(self, mock_config, httpx_mock):
        """Test request method adds Authorization header."""
        httpx_mock.add_response(
            method="GET", url="https://api.example.com/test", status_code=200
        )

        client = AmigoHttpClient(mock_config)

        # Mock token that won't expire
        fresh_token = Mock(
            id_token="test-bearer-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        with patch("src.http_client.sign_in_with_api_key", return_value=fresh_token):
            await client.request("GET", "/test")

        request = httpx_mock.get_request()
        assert request.headers["Authorization"] == "Bearer test-bearer-token"

    @pytest.mark.asyncio
    async def test_request_retries_on_401(self, mock_config, httpx_mock):
        """Test request retries once on 401 response."""
        # First request returns 401, second succeeds
        httpx_mock.add_response(
            method="GET", url="https://api.example.com/test", status_code=401
        )
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/test",
            status_code=200,
            json={"success": True},
        )

        client = AmigoHttpClient(mock_config)

        fresh_token = Mock(
            id_token="fresh-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        with patch("src.http_client.sign_in_with_api_key", return_value=fresh_token):
            response = await client.request("GET", "/test")

        assert response.status_code == 200
        # After 401, token should be refreshed (not None, but fresh)
        assert client._token.id_token == "fresh-token"

    @pytest.mark.asyncio
    async def test_request_raises_error_for_non_2xx(self, mock_config, httpx_mock):
        """Test request raises error for non-2xx responses."""
        httpx_mock.add_response(
            method="GET",
            url="https://api.example.com/test",
            status_code=400,
            text="Bad Request",
        )

        client = AmigoHttpClient(mock_config)

        fresh_token = Mock(
            id_token="test-bearer-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        with patch("src.http_client.sign_in_with_api_key", return_value=fresh_token):
            with pytest.raises(BadRequestError):
                await client.request("GET", "/test")

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_config):
        """Test client works as async context manager."""
        async with AmigoHttpClient(mock_config) as client:
            assert isinstance(client, AmigoHttpClient)

        # Client should be closed after context exit
        assert client._client.is_closed

    @pytest.mark.asyncio
    async def test_stream_lines_yields_and_sets_headers(self, mock_config):
        client = AmigoHttpClient(mock_config)

        async with mock_http_stream(
            [" line1 ", "", "line2\n", " "], status_code=200
        ) as tracker:
            lines = []
            async for ln in client.stream_lines("GET", "/stream-test"):
                lines.append(ln)

        assert lines == ["line1", "line2"]
        headers = tracker["last_call"]["headers"]
        assert headers["Authorization"] == "Bearer test-bearer-token"
        assert headers["Accept"] == "application/x-ndjson"

    @pytest.mark.asyncio
    async def test_stream_lines_retries_once_on_401(self, mock_config):
        client = AmigoHttpClient(mock_config)

        async with mock_http_stream_sequence([(401, []), (200, ["ok"])]) as tracker:
            lines = []
            async for ln in client.stream_lines("GET", "/retry-401"):
                lines.append(ln)

        assert tracker["call_count"] == 2
        assert lines == ["ok"]

    @pytest.mark.asyncio
    async def test_stream_lines_raises_on_non_2xx(self, mock_config):
        client = AmigoHttpClient(mock_config)

        async with mock_http_stream([], status_code=404):
            with pytest.raises(NotFoundError):
                async for _ in client.stream_lines("GET", "/not-found"):
                    pass
