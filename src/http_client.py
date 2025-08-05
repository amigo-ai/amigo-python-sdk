import datetime as dt
from typing import Any, Optional

import httpx
from src.auth import sign_in_with_api_key
from src.config import AmigoConfig
from src.errors import AuthenticationError, raise_for_status
from src.generated.model import SrcAppEndpointsUserSignInWithApiKeyResponse


class AmigoHttpClient:
    def __init__(self, cfg: AmigoConfig, **httpx_kwargs: Any) -> None:
        self._cfg = cfg
        self._token: Optional[SrcAppEndpointsUserSignInWithApiKeyResponse] = None
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

    async def aclose(self) -> None:
        await self._client.aclose()

    # async-context-manager sugar
    async def __aenter__(self):  # → async with AmigoHTTPClient(...) as http:
        return self

    async def __aexit__(self, *_):
        await self.aclose()
