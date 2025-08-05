from typing import Any, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class AmigoConfig(BaseSettings):
    """
    Configuration for the Amigo API client.
    
    Can be configured via constructor parameters or environment variables:
    - AMIGO_API_KEY
    - AMIGO_API_KEY_ID  
    - AMIGO_USER_ID
    - AMIGO_BASE_URL
    """
    api_key: str = Field(..., alias="API_KEY", description="API key for authentication")
    api_key_id: str = Field(..., alias="API_KEY_ID", description="API key ID for authentication")
    user_id: str = Field(..., alias="USER_ID", description="User ID for API requests")
    base_url: str = Field(
        default="https://api.amigo.ai", 
        alias="BASE_URL",
        description="Base URL for the Amigo API"
    )
    
    model_config = {
        "env_prefix": "AMIGO_",
        "case_sensitive": False,
        "validate_assignment": True,
        "frozen": True
    }


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
        base_url: Optional[str] = None,
        config: Optional[AmigoConfig] = None
    ):
        """
        Initialize the Amigo SDK client.
        
        Args:
            api_key: API key for authentication (or set AMIGO_API_KEY env var)
            api_key_id: API key ID for authentication (or set AMIGO_API_KEY_ID env var)
            user_id: User ID for API requests (or set AMIGO_USER_ID env var)
            base_url: Base URL for the API (or set AMIGO_BASE_URL env var)
            config: Pre-configured AmigoConfig instance (overrides individual params)
        """
        if config:
            self._cfg = config
        else:
            # Build config from individual parameters, falling back to env vars
            cfg_dict: dict[str, Any] = {k: v for k, v in [
                ("api_key", api_key),
                ("api_key_id", api_key_id),
                ("user_id", user_id),
                ("base_url", base_url),
            ] if v is not None}
                
        try:
            self._cfg = AmigoConfig(**cfg_dict)
        except Exception as e:
            raise ValueError(
                "AmigoClient configuration incomplete. "
                "Provide api_key, api_key_id, user_id, base_url "
                "either as kwargs or environment variables."
            ) from e

        # TODO: pass self._cfg to transport layer here
        # self.http = AmigoHTTPClient(**self._cfg.dict())

    @property
    def config(self) -> AmigoConfig:
        """Access the configuration object."""
        return self._cfg
    
    
