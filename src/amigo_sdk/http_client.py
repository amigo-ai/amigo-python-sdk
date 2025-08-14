import asyncio
import datetime as dt
from collections.abc import AsyncIterator
from typing import Any, Optional

import httpx

from amigo_sdk.auth import sign_in_with_api_key
from amigo_sdk.config import AmigoConfig
from amigo_sdk.errors import (
    AuthenticationError,
    get_error_class_for_status_code,
    raise_for_status,
)
from amigo_sdk.generated.model import UserSignInWithApiKeyResponse


class AmigoHttpClient:
    def __init__(self, cfg: AmigoConfig, **httpx_kwargs: Any) -> None:
        self._cfg = cfg
        self._token: Optional[UserSignInWithApiKeyResponse] = None
        self._client = httpx.AsyncClient(
            base_url=cfg.base_url,
            **httpx_kwargs,
        )

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
        kwargs["headers"]["Authorization"] = f"Bearer {await self._ensure_token()}"

        resp = await self._client.request(method, path, **kwargs)

        # On 401 refresh token once and retry
        if resp.status_code == 401:
            self._token = None
            kwargs["headers"]["Authorization"] = f"Bearer {await self._ensure_token()}"
            resp = await self._client.request(method, path, **kwargs)

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

        async def _raise_light_if_error(resp: httpx.Response) -> None:
            if 200 <= resp.status_code < 300:
                return
            error_class = get_error_class_for_status_code(resp.status_code)
            # Avoid consuming the stream body for error reporting
            raise error_class(
                f"HTTP {resp.status_code} error", status_code=resp.status_code
            )

        async def _yield_from_response(resp: httpx.Response) -> AsyncIterator[str]:
            await _raise_light_if_error(resp)
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
