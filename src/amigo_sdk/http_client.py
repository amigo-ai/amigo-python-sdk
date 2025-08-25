import asyncio
import datetime as dt
import random
import time
from collections.abc import AsyncIterator, Iterator
from email.utils import parsedate_to_datetime
from typing import Any, Optional

import httpx

from amigo_sdk.auth import sign_in_with_api_key, sign_in_with_api_key_sync
from amigo_sdk.config import AmigoConfig
from amigo_sdk.errors import (
    AuthenticationError,
    get_error_class_for_status_code,
    raise_for_status,
)
from amigo_sdk.generated.model import UserSignInWithApiKeyResponse


class AmigoHttpClient:
    def __init__(
        self,
        cfg: AmigoConfig,
        *,
        retry_max_attempts: int = 3,
        retry_backoff_base: float = 0.25,
        retry_max_delay_seconds: float = 30.0,
        retry_on_status: set[int] | None = None,
        retry_on_methods: set[str] | None = None,
        **httpx_kwargs: Any,
    ) -> None:
        self._cfg = cfg
        self._token: Optional[UserSignInWithApiKeyResponse] = None
        self._client = httpx.AsyncClient(
            base_url=cfg.base_url,
            **httpx_kwargs,
        )
        # Retry configuration
        self._retry_max_attempts = max(1, retry_max_attempts)
        self._retry_backoff_base = retry_backoff_base
        self._retry_max_delay_seconds = max(0.0, retry_max_delay_seconds)
        self._retry_on_status = retry_on_status or {408, 429, 500, 502, 503, 504}
        # Default to GET only; POST is handled specially for 429 + Retry-After
        self._retry_on_methods = {m.upper() for m in (retry_on_methods or {"GET"})}

    def _is_retryable_method(self, method: str) -> bool:
        return method.upper() in self._retry_on_methods

    def _is_retryable_response(self, method: str, resp: httpx.Response) -> bool:
        status = resp.status_code
        # Allow POST retry only for 429 when Retry-After header is present
        if (
            method.upper() == "POST"
            and status == 429
            and resp.headers.get("Retry-After")
        ):
            return True
        return self._is_retryable_method(method) and status in self._retry_on_status

    def _parse_retry_after_seconds(self, resp: httpx.Response) -> float | None:
        retry_after = resp.headers.get("Retry-After")
        if not retry_after:
            return None
        # Numeric seconds
        try:
            seconds = float(retry_after)
            return max(0.0, seconds)
        except ValueError:
            pass
        # HTTP-date format
        try:
            target_dt = parsedate_to_datetime(retry_after)
            if target_dt is None:
                return None
            if target_dt.tzinfo is None:
                target_dt = target_dt.replace(tzinfo=dt.UTC)
            now = dt.datetime.now(dt.UTC)
            delta_seconds = (target_dt - now).total_seconds()
            return max(0.0, delta_seconds)
        except Exception:
            return None

    def _retry_delay_seconds(self, attempt: int, resp: httpx.Response | None) -> float:
        # Honor Retry-After when present (numeric or HTTP-date), clamped by max delay
        if resp is not None:
            ra_seconds = self._parse_retry_after_seconds(resp)
            if ra_seconds is not None:
                return min(self._retry_max_delay_seconds, ra_seconds)
        # Exponential backoff with full jitter: U(0, min(cap, base * 2^(attempt-1)))
        window = self._retry_backoff_base * (2 ** (attempt - 1))
        window = min(window, self._retry_max_delay_seconds)
        return random.uniform(0.0, window)

    async def _ensure_token(self) -> str:
        """Fetch or refresh bearer token ~5 min before expiry."""
        if not self._token or dt.datetime.now(
            dt.UTC
        ) > self._token.expires_at - dt.timedelta(minutes=5):
            try:
                self._token = await sign_in_with_api_key(self._cfg)
            except Exception as e:
                raise AuthenticationError(
                    "API-key exchange failed",
                ) from e

        return self._token.id_token

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        kwargs.setdefault("headers", {})
        attempt = 1

        while True:
            kwargs["headers"]["Authorization"] = f"Bearer {await self._ensure_token()}"

            resp: httpx.Response | None = None
            try:
                resp = await self._client.request(method, path, **kwargs)

                # On 401 refresh token once and retry immediately
                if resp.status_code == 401:
                    self._token = None
                    kwargs["headers"]["Authorization"] = (
                        f"Bearer {await self._ensure_token()}"
                    )
                    resp = await self._client.request(method, path, **kwargs)

            except (httpx.TimeoutException, httpx.TransportError):
                # Retry only if method is allowed (e.g., GET); POST not retried for transport/timeouts
                if (
                    not self._is_retryable_method(method)
                    or attempt >= self._retry_max_attempts
                ):
                    raise
                await asyncio.sleep(self._retry_delay_seconds(attempt, None))
                attempt += 1
                continue

            # Retry on configured HTTP status codes
            if (
                self._is_retryable_response(method, resp)
                and attempt < self._retry_max_attempts
            ):
                await asyncio.sleep(self._retry_delay_seconds(attempt, resp))
                attempt += 1
                continue

            # Check response status and raise appropriate errors
            raise_for_status(resp)
            return resp

    async def stream_lines(
        self,
        method: str,
        path: str,
        abort_event: asyncio.Event | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream response lines without buffering the full body.

        - Adds Authorization and sensible streaming headers
        - Retries once on 401 by refreshing the token
        - Raises mapped errors for non-2xx without consuming the body
        """
        kwargs.setdefault("headers", {})
        headers = kwargs["headers"]
        headers["Authorization"] = f"Bearer {await self._ensure_token()}"
        headers.setdefault("Accept", "application/x-ndjson")

        async def _raise_status_with_body(resp: httpx.Response) -> None:
            """Ensure response body is buffered, then raise mapped error with details."""
            if 200 <= resp.status_code < 300:
                return
            # Fully buffer the body so raise_for_status() can extract JSON/text safely
            try:
                await resp.aread()
            except Exception:
                pass
            # If this is a real httpx.Response, use our rich raise_for_status
            if hasattr(resp, "is_success"):
                raise_for_status(resp)
            # Otherwise, fall back to lightweight error mapping used in tests' mock responses
            error_class = get_error_class_for_status_code(
                getattr(resp, "status_code", 0)
            )
            raise error_class(
                f"HTTP {getattr(resp, 'status_code', 'unknown')} error",
                status_code=getattr(resp, "status_code", None),
            )

        async def _yield_from_response(resp: httpx.Response) -> AsyncIterator[str]:
            await _raise_status_with_body(resp)
            if abort_event and abort_event.is_set():
                return
            async for line in resp.aiter_lines():
                if abort_event and abort_event.is_set():
                    return
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                yield line_stripped

        # First attempt
        if abort_event and abort_event.is_set():
            return
        async with self._client.stream(method, path, **kwargs) as resp:
            if resp.status_code == 401:
                # Refresh token and retry once
                self._token = None
                headers["Authorization"] = f"Bearer {await self._ensure_token()}"
                if abort_event and abort_event.is_set():
                    return
                async with self._client.stream(method, path, **kwargs) as retry_resp:
                    async for ln in _yield_from_response(retry_resp):
                        yield ln
                return

            async for ln in _yield_from_response(resp):
                yield ln

    async def aclose(self) -> None:
        await self._client.aclose()

    # async-context-manager sugar
    async def __aenter__(self):  # → async with AmigoHTTPClient(...) as http:
        return self

    async def __aexit__(self, *_):
        await self.aclose()


class AmigoSyncHttpClient:
    def __init__(
        self,
        cfg: AmigoConfig,
        *,
        retry_max_attempts: int = 3,
        retry_backoff_base: float = 0.25,
        retry_max_delay_seconds: float = 30.0,
        retry_on_status: set[int] | None = None,
        retry_on_methods: set[str] | None = None,
        **httpx_kwargs: Any,
    ) -> None:
        self._cfg = cfg
        self._token: Optional[UserSignInWithApiKeyResponse] = None
        self._client = httpx.Client(base_url=cfg.base_url, **httpx_kwargs)
        # Retry configuration
        self._retry_max_attempts = max(1, retry_max_attempts)
        self._retry_backoff_base = retry_backoff_base
        self._retry_max_delay_seconds = max(0.0, retry_max_delay_seconds)
        self._retry_on_status = retry_on_status or {408, 429, 500, 502, 503, 504}
        # Default to GET only; POST is handled specially for 429 + Retry-After
        self._retry_on_methods = {m.upper() for m in (retry_on_methods or {"GET"})}

    def _is_retryable_method(self, method: str) -> bool:
        return method.upper() in self._retry_on_methods

    def _is_retryable_response(self, method: str, resp: httpx.Response) -> bool:
        status = resp.status_code
        if (
            method.upper() == "POST"
            and status == 429
            and resp.headers.get("Retry-After")
        ):
            return True
        return self._is_retryable_method(method) and status in self._retry_on_status

    def _parse_retry_after_seconds(self, resp: httpx.Response) -> float | None:
        retry_after = resp.headers.get("Retry-After")
        if not retry_after:
            return None
        try:
            seconds = float(retry_after)
            return max(0.0, seconds)
        except ValueError:
            pass
        try:
            target_dt = parsedate_to_datetime(retry_after)
            if target_dt is None:
                return None
            if target_dt.tzinfo is None:
                target_dt = target_dt.replace(tzinfo=dt.UTC)
            now = dt.datetime.now(dt.UTC)
            delta_seconds = (target_dt - now).total_seconds()
            return max(0.0, delta_seconds)
        except Exception:
            return None

    def _retry_delay_seconds(self, attempt: int, resp: httpx.Response | None) -> float:
        if resp is not None:
            ra_seconds = self._parse_retry_after_seconds(resp)
            if ra_seconds is not None:
                return min(self._retry_max_delay_seconds, ra_seconds)
        window = self._retry_backoff_base * (2 ** (attempt - 1))
        window = min(window, self._retry_max_delay_seconds)
        return random.uniform(0.0, window)

    def _ensure_token(self) -> str:
        if not self._token or dt.datetime.now(
            dt.UTC
        ) > self._token.expires_at - dt.timedelta(minutes=5):
            try:
                self._token = sign_in_with_api_key_sync(self._cfg)
            except Exception as e:
                raise AuthenticationError("API-key exchange failed") from e
        return self._token.id_token

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        kwargs.setdefault("headers", {})
        attempt = 1

        while True:
            kwargs["headers"]["Authorization"] = f"Bearer {self._ensure_token()}"

            resp: httpx.Response | None = None
            try:
                resp = self._client.request(method, path, **kwargs)
                if resp.status_code == 401:
                    self._token = None
                    kwargs["headers"]["Authorization"] = (
                        f"Bearer {self._ensure_token()}"
                    )
                    resp = self._client.request(method, path, **kwargs)

            except (httpx.TimeoutException, httpx.TransportError):
                if (
                    not self._is_retryable_method(method)
                ) or attempt >= self._retry_max_attempts:
                    raise
                time.sleep(self._retry_delay_seconds(attempt, None))
                attempt += 1
                continue

            if (
                self._is_retryable_response(method, resp)
                and attempt < self._retry_max_attempts
            ):
                time.sleep(self._retry_delay_seconds(attempt, resp))
                attempt += 1
                continue

            raise_for_status(resp)
            return resp

    def stream_lines(
        self,
        method: str,
        path: str,
        abort_flag: list[bool] | None = None,
        **kwargs,
    ) -> Iterator[str]:
        kwargs.setdefault("headers", {})
        headers = kwargs["headers"]
        headers["Authorization"] = f"Bearer {self._ensure_token()}"
        headers.setdefault("Accept", "application/x-ndjson")

        def _raise_status_with_body(resp: httpx.Response) -> None:
            if 200 <= resp.status_code < 300:
                return
            try:
                _ = resp.text
            except Exception:
                pass
            if hasattr(resp, "is_success"):
                raise_for_status(resp)
            error_class = get_error_class_for_status_code(
                getattr(resp, "status_code", 0)
            )
            raise error_class(
                f"HTTP {getattr(resp, 'status_code', 'unknown')} error",
                status_code=getattr(resp, "status_code", None),
            )

        def _yield_from_response(resp: httpx.Response) -> Iterator[str]:
            _raise_status_with_body(resp)
            if abort_flag and abort_flag[0]:
                return
            for line in resp.iter_lines():
                if abort_flag and abort_flag[0]:
                    return
                line_stripped = (line or "").strip()
                if not line_stripped:
                    continue
                yield line_stripped

        if abort_flag and abort_flag[0]:
            return iter(())
        with self._client.stream(method, path, **kwargs) as resp:
            if resp.status_code == 401:
                self._token = None
                headers["Authorization"] = f"Bearer {self._ensure_token()}"
                if abort_flag and abort_flag[0]:
                    return iter(())
                with self._client.stream(method, path, **kwargs) as retry_resp:
                    for ln in _yield_from_response(retry_resp):
                        yield ln
                return

            for ln in _yield_from_response(resp):
                yield ln

    def aclose(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.aclose()
