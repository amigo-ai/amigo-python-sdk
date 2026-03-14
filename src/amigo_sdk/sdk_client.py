from typing import Any

from amigo_sdk.config import AmigoConfig
from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient
from amigo_sdk.resources.agent import AgentResource, AsyncAgentResource
from amigo_sdk.resources.context_graph import (
    AsyncContextGraphResource,
    ContextGraphResource,
)
from amigo_sdk.resources.conversation import (
    AsyncConversationResource,
    ConversationResource,
)
from amigo_sdk.resources.organization import (
    AsyncOrganizationResource,
    OrganizationResource,
)
from amigo_sdk.resources.service import AsyncServiceResource, ServiceResource
from amigo_sdk.resources.user import AsyncUserResource, UserResource


class AsyncAmigoClient:
    """Amigo API client (asynchronous)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_key_id: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
        base_url: str | None = None,
        config: AmigoConfig | None = None,
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
        self._http = AmigoAsyncHttpClient(self._cfg, **httpx_kwargs)
        self._organizations = AsyncOrganizationResource(
            self._http, self._cfg.organization_id
        )
        self._services = AsyncServiceResource(self._http, self._cfg.organization_id)
        self._conversations = AsyncConversationResource(
            self._http, self._cfg.organization_id
        )
        self._users = AsyncUserResource(self._http, self._cfg.organization_id)
        self._agents = AsyncAgentResource(self._http, self._cfg.organization_id)
        self._context_graphs = AsyncContextGraphResource(
            self._http, self._cfg.organization_id
        )

    @property
    def config(self) -> AmigoConfig:
        """Access the configuration object."""
        return self._cfg

    @property
    def organizations(self) -> AsyncOrganizationResource:
        """Access organization resource."""
        return self._organizations

    @property
    def agents(self) -> AsyncAgentResource:
        """Access agent resource."""
        return self._agents

    @property
    def context_graphs(self) -> AsyncContextGraphResource:
        """Access context graph (HSM) resource."""
        return self._context_graphs

    @property
    def services(self) -> AsyncServiceResource:
        """Access service resource."""
        return self._services

    @property
    def conversations(self) -> AsyncConversationResource:
        """Access conversation resource."""
        return self._conversations

    @property
    def users(self) -> AsyncUserResource:
        """Access user resource."""
        return self._users

    async def aclose(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()

    # async-context-manager sugar
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.aclose()


class AmigoClient:
    """Amigo API client (synchronous)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_key_id: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
        base_url: str | None = None,
        config: AmigoConfig | None = None,
        **httpx_kwargs: Any,
    ):
        """Initialize the Amigo SDK client.

        Args:
            api_key: API key for authentication (or set AMIGO_API_KEY env var)
            api_key_id: API key ID for authentication (or set AMIGO_API_KEY_ID env var)
            user_id: User ID for API requests (or set AMIGO_USER_ID env var)
            organization_id: Organization ID for API requests (or set AMIGO_ORGANIZATION_ID env var)
            base_url: Base URL for the API (or set AMIGO_BASE_URL env var)
            config: Pre-configured AmigoConfig instance (overrides individual params)
            **httpx_kwargs: Additional arguments passed to httpx.Client
        """
        if config:
            self._cfg = config
        else:
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

        self._http = AmigoHttpClient(self._cfg, **httpx_kwargs)
        self._organizations = OrganizationResource(
            self._http, self._cfg.organization_id
        )
        self._services = ServiceResource(self._http, self._cfg.organization_id)
        self._conversations = ConversationResource(
            self._http, self._cfg.organization_id
        )
        self._users = UserResource(self._http, self._cfg.organization_id)
        self._agents = AgentResource(self._http, self._cfg.organization_id)
        self._context_graphs = ContextGraphResource(
            self._http, self._cfg.organization_id
        )

    @property
    def config(self) -> AmigoConfig:
        """Access the configuration object."""
        return self._cfg

    @property
    def organizations(self) -> OrganizationResource:
        """Access organization resource."""
        return self._organizations

    @property
    def agents(self) -> AgentResource:
        """Access agent resource."""
        return self._agents

    @property
    def context_graphs(self) -> ContextGraphResource:
        """Access context graph (HSM) resource."""
        return self._context_graphs

    @property
    def services(self) -> ServiceResource:
        """Access service resource."""
        return self._services

    @property
    def conversations(self) -> ConversationResource:
        """Access conversation resource."""
        return self._conversations

    @property
    def users(self) -> UserResource:
        """Access user resource."""
        return self._users

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
