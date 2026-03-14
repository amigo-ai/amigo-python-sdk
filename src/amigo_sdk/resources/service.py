from amigo_sdk.generated.model import (
    GetServicesParametersQuery,
    ServiceGetServicesResponse,
)
from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient


class AsyncServiceResource:
    """Service resource for Amigo API operations."""

    def __init__(self, http_client: AmigoAsyncHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    async def get_services(
        self, params: GetServicesParametersQuery | None = None
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

    async def list(
        self, params: GetServicesParametersQuery | None = None
    ) -> ServiceGetServicesResponse:
        """Alias for get_services."""
        return await self.get_services(params)


class ServiceResource:
    """Service resource for synchronous operations."""

    def __init__(self, http_client: AmigoHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    def get_services(
        self, params: GetServicesParametersQuery | None = None
    ) -> ServiceGetServicesResponse:
        """Get all services for the organization."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/service/",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return ServiceGetServicesResponse.model_validate_json(response.text)

    def list(
        self, params: GetServicesParametersQuery | None = None
    ) -> ServiceGetServicesResponse:
        """Alias for get_services."""
        return self.get_services(params)
