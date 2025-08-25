from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import Mock, patch

import httpx
import pytest

from amigo_sdk.config import AmigoConfig
from amigo_sdk.errors import (
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from amigo_sdk.http_client import AmigoSyncHttpClient


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
class TestAmigoSyncHttpClient:
    def test_client_initialization(self, mock_config):
        client = AmigoSyncHttpClient(mock_config, timeout=30)
        assert client._cfg == mock_config
        assert client._token is None
        assert str(client._client.base_url) == "https://api.example.com"

    def test_ensure_token_fetches_new_token(self, mock_config, mock_token_response):
        client = AmigoSyncHttpClient(mock_config)

        with patch(
            "amigo_sdk.http_client.sign_in_with_api_key_sync",
            return_value=mock_token_response,
        ):
            token = client._ensure_token()

        assert token == "test-bearer-token"
        assert client._token == mock_token_response

    def test_ensure_token_refreshes_expired_token(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)

        expired_token = Mock(
            id_token="expired-token",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        )
        client._token = expired_token

        fresh_token = Mock(
            id_token="fresh-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        with patch(
            "amigo_sdk.http_client.sign_in_with_api_key_sync", return_value=fresh_token
        ):
            token = client._ensure_token()

        assert token == "fresh-token"
        assert client._token == fresh_token

    def test_ensure_token_handles_auth_failure(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)

        with patch(
            "amigo_sdk.http_client.sign_in_with_api_key_sync",
            side_effect=Exception("Auth failed"),
        ):
            with pytest.raises(AuthenticationError):
                client._ensure_token()

    def test_request_adds_authorization_header(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)

        fresh_token = Mock(
            id_token="test-bearer-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", return_value=httpx.Response(200)),
        ):
            client.request("GET", "/test")

        assert client._token.id_token == "test-bearer-token"

    def test_request_retries_on_401(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)
        fresh_token = Mock(
            id_token="fresh-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        seq = [httpx.Response(401), httpx.Response(200, json={"ok": True})]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
        ):
            resp = client.request("GET", "/test")

        assert resp.status_code == 200
        assert client._token.id_token == "fresh-token"

    def test_request_raises_error_for_non_2xx(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)
        fresh_token = Mock(
            id_token="tok",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", return_value=httpx.Response(400)),
        ):
            with pytest.raises(BadRequestError):
                client.request("GET", "/bad")

    def test_sync_context_manager(self, mock_config):
        with AmigoSyncHttpClient(mock_config) as client:
            assert isinstance(client, AmigoSyncHttpClient)

        assert client._client.is_closed

    def test_stream_lines_yields_and_sets_headers(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)

        class _Resp:
            def __init__(self):
                self.status_code = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def iter_lines(self):
                yield " line1 "
                yield ""
                yield "line2\n"
                yield " "

        fresh_token = Mock(
            id_token="tok",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "stream", return_value=_Resp()),
        ):
            lines = list(client.stream_lines("GET", "/stream"))

        assert lines == ["line1", "line2"]

    def test_stream_lines_retries_once_on_401(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)

        class _Resp:
            def __init__(self, status_code, lines):
                self.status_code = status_code
                self._lines = lines

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def iter_lines(self):
                yield from self._lines

        seq = [_Resp(401, []), _Resp(200, ["ok"])]

        def fake_stream(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        fresh_token = Mock(
            id_token="tok",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "stream", new=fake_stream),
        ):
            lines = list(client.stream_lines("GET", "/retry"))

        assert lines == ["ok"]

    def test_stream_lines_raises_on_non_2xx(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)

        class _Resp:
            def __init__(self):
                self.status_code = 404

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def iter_lines(self):
                yield from ()

        fresh_token = Mock(
            id_token="tok",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "stream", return_value=_Resp()),
        ):
            with pytest.raises(NotFoundError):
                list(client.stream_lines("GET", "/not-found"))

    def test_request_retries_on_408_get(self, mock_config):
        client = AmigoSyncHttpClient(mock_config, retry_max_attempts=3)
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        seq = [httpx.Response(408), httpx.Response(200)]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        sleeps: list[float] = []

        def fake_sleep(seconds: float):
            sleeps.append(seconds)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
            patch("time.sleep", new=fake_sleep),
        ):
            resp = client.request("GET", "/r408")

        assert resp.status_code == 200
        assert len(sleeps) == 1

    def test_request_retries_on_5xx_get(self, mock_config):
        client = AmigoSyncHttpClient(mock_config, retry_max_attempts=3)
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        seq = [httpx.Response(500), httpx.Response(200)]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        sleeps: list[float] = []

        def fake_sleep(seconds: float):
            sleeps.append(seconds)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
            patch("time.sleep", new=fake_sleep),
        ):
            resp = client.request("GET", "/r500")

        assert resp.status_code == 200
        assert len(sleeps) == 1

    def test_request_retries_on_429_get_respects_retry_after_seconds(self, mock_config):
        client = AmigoSyncHttpClient(
            mock_config, retry_max_attempts=3, retry_max_delay_seconds=10.0
        )
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        ra = {"Retry-After": "1.5"}
        seq = [httpx.Response(429, headers=ra), httpx.Response(200)]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        sleeps: list[float] = []

        def fake_sleep(seconds: float):
            sleeps.append(seconds)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
            patch("time.sleep", new=fake_sleep),
        ):
            resp = client.request("GET", "/r429s")

        assert resp.status_code == 200
        assert len(sleeps) == 1
        assert sleeps[0] == pytest.approx(1.5, rel=1e-3)

    def test_request_retries_on_429_post_with_retry_after_seconds(self, mock_config):
        client = AmigoSyncHttpClient(mock_config, retry_max_attempts=3)
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        ra = {"Retry-After": "0.5"}
        seq = [httpx.Response(429, headers=ra), httpx.Response(200)]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        sleeps: list[float] = []

        def fake_sleep(seconds: float):
            sleeps.append(seconds)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
            patch("time.sleep", new=fake_sleep),
        ):
            resp = client.request("POST", "/r429p")

        assert resp.status_code == 200
        assert len(sleeps) == 1
        assert sleeps[0] == pytest.approx(0.5, rel=1e-3)

    def test_request_retries_on_429_post_with_retry_after_http_date(self, mock_config):
        future_dt = datetime.now(timezone.utc) + timedelta(seconds=3)
        http_date = format_datetime(future_dt)
        client = AmigoSyncHttpClient(
            mock_config, retry_max_attempts=3, retry_max_delay_seconds=30.0
        )
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        ra = {"Retry-After": http_date}
        seq = [httpx.Response(429, headers=ra), httpx.Response(200)]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        sleeps: list[float] = []

        def fake_sleep(seconds: float):
            sleeps.append(seconds)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
            patch("time.sleep", new=fake_sleep),
        ):
            resp = client.request("POST", "/r429pdate")

        assert resp.status_code == 200
        assert len(sleeps) == 1
        assert sleeps[0] == pytest.approx(3.0, abs=1.0)

    def test_request_does_not_retry_post_429_without_retry_after(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        seq = [httpx.Response(429)]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        sleeps: list[float] = []

        def fake_sleep(seconds: float):
            sleeps.append(seconds)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
            patch("time.sleep", new=fake_sleep),
        ):
            with pytest.raises(RateLimitError):
                client.request("POST", "/r429pnora")

        assert sleeps == []

    def test_request_retries_on_timeout_get(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        seq = [httpx.ReadTimeout("boom"), httpx.Response(200)]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            resp = seq.pop(0)
            if isinstance(resp, Exception):
                raise resp
            return resp

        sleeps: list[float] = []

        def fake_sleep(seconds: float):
            sleeps.append(seconds)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
            patch("time.sleep", new=fake_sleep),
        ):
            resp = client.request("GET", "/timeout")

        assert resp.status_code == 200
        assert len(sleeps) == 1

    def test_request_does_not_retry_post_on_timeout_by_default(self, mock_config):
        client = AmigoSyncHttpClient(mock_config)
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            raise httpx.ReadTimeout("boom")

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
        ):
            with pytest.raises(httpx.TimeoutException):
                client.request("POST", "/timeout-post")

    def test_backoff_clamps_to_max_delay(self, mock_config):
        client = AmigoSyncHttpClient(
            mock_config, retry_backoff_base=100.0, retry_max_delay_seconds=0.5
        )
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        seq = [httpx.Response(500), httpx.Response(200)]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        sleeps: list[float] = []

        def fake_sleep(seconds: float):
            sleeps.append(seconds)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
            patch("time.sleep", new=fake_sleep),
            patch("random.uniform", side_effect=lambda a, b: b),
        ):
            resp = client.request("GET", "/clamp")

        assert resp.status_code == 200
        assert len(sleeps) == 1
        assert sleeps[0] == 0.5

    def test_max_attempts_limits_retries(self, mock_config):
        client = AmigoSyncHttpClient(mock_config, retry_max_attempts=3)
        fresh_token = Mock(
            id_token="tok", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        seq = [httpx.Response(500), httpx.Response(500), httpx.Response(500)]

        def fake_request(self, method, url, **kwargs):  # noqa: ANN001
            return seq.pop(0)

        sleeps: list[float] = []

        def fake_sleep(seconds: float):
            sleeps.append(seconds)

        with (
            patch(
                "amigo_sdk.http_client.sign_in_with_api_key_sync",
                return_value=fresh_token,
            ),
            patch.object(httpx.Client, "request", new=fake_request),
            patch("time.sleep", new=fake_sleep),
        ):
            with pytest.raises(ServerError):
                client.request("GET", "/max")

        assert len(sleeps) == 2
