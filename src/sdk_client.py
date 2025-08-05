from typing import Any, Optional

from src.config import AmigoConfig
from src.http_client import AmigoHttpClient
from src.resources.organization import OrganizationResource
from src.resources.service import ServiceResource


class AmigoClient:
    """
    Amigo API client
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        api_key_id: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[AmigoConfig] = None,
        **httpx_kwargs: Any,
    ):
        """
        Initialize the Amigo SDK client.

        Args:
            api_key: API key for authentication (or set AMIGO_API_KEY env var)
            api_key_id: API key ID for authentication (or set AMIGO_API_KEY_ID env var)
            user_id: User ID for API requests (or set AMIGO_USER_ID env var)
            organization_id: Organization ID for API requests (or set AMIGO_ORGANIZATION_ID env var)
            base_url: Base URL for the API (or set AMIGO_BASE_URL env var)
            config: Pre-configured AmigoConfig instance (overrides individual params)
            **httpx_kwargs: Additional arguments passed to httpx.AsyncClient
        """
        if config:
            self._cfg = config
        else:
            # Build config from individual parameters, falling back to env vars
            cfg_dict: dict[str, Any] = {
                k: v
                for k, v in [
                    ("api_key", api_key),
                    ("api_key_id", api_key_id),
                    ("user_id", user_id),
                    ("organization_id", organization_id),
                    ("base_url", base_url),
                ]
                if v is not None
            }

            try:
                self._cfg = AmigoConfig(**cfg_dict)
            except Exception as e:
                raise ValueError(
                    "AmigoClient configuration incomplete. "
                    "Provide api_key, api_key_id, user_id, organization_id, base_url "
                    "either as kwargs or environment variables."
                ) from e

        # Initialize HTTP client and resources
        self._http = AmigoHttpClient(self._cfg, **httpx_kwargs)
        self._organization = OrganizationResource(self._http, self._cfg.organization_id)
        self._service = ServiceResource(self._http, self._cfg.organization_id)

    @property
    def config(self) -> AmigoConfig:
        """Access the configuration object."""
        return self._cfg

    @property
    def organization(self) -> OrganizationResource:
        """Access organization resource."""
        return self._organization

    @property
    def service(self) -> ServiceResource:
        """Access service resource."""
        return self._service

    async def aclose(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()

    # async-context-manager sugar
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.aclose()
