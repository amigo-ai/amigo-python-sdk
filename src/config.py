from typing import Any
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
    - AMIGO_ORGANIZATION_ID
    """

    api_key: str = Field(..., description="API key for authentication")
    api_key_id: str = Field(..., description="API key ID for authentication")
    user_id: str = Field(..., description="User ID for API requests")
    organization_id: str = Field(..., description="Organization ID for API requests")
    base_url: str = Field(
        default="https://api.amigo.ai",
        description="Base URL for the Amigo API",
    )

    model_config = {
        "env_prefix": "AMIGO_",
        "case_sensitive": False,
        "validate_assignment": True,
        "frozen": True,
    }
