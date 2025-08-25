from typing import Optional

from amigo_sdk.generated.model import (
    GetServicesParametersQuery,
    ServiceGetServicesResponse,
)
from amigo_sdk.http_client import AmigoHttpClient, AmigoSyncHttpClient


class ServiceResource:
    """Service resource for Amigo API operations."""

    def __init__(
        self, http_client: AmigoHttpClient, organization_id: str
    ) -> ServiceGetServicesResponse:
        self._http = http_client
        self._organization_id = organization_id

    async def get_services(
        self, params: Optional[GetServicesParametersQuery] = None
    ) -> ServiceGetServicesResponse:
        """Get all services."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/service/",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return ServiceGetServicesResponse.model_validate_json(response.text)


class SyncServiceResource:
    def __init__(self, http_client: AmigoSyncHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    def get_services(
        self, params: Optional[GetServicesParametersQuery] = None
    ) -> ServiceGetServicesResponse:
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/service/",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return ServiceGetServicesResponse.model_validate_json(response.text)
