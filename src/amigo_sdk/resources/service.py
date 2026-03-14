from amigo_sdk.generated.model import (
    GetServicesParametersQuery,
    ServiceCreateServiceRequest,
    ServiceCreateServiceResponse,
    ServiceGetServicesResponse,
    ServiceUpdateServiceRequest,
    ServiceUpsertServiceVersionSetRequest,
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
        """List services for the organization."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/service/",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return ServiceGetServicesResponse.model_validate_json(response.text)

    async def create_service(
        self, body: ServiceCreateServiceRequest
    ) -> ServiceCreateServiceResponse:
        """Create a new service."""
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/service/",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return ServiceCreateServiceResponse.model_validate_json(response.text)

    async def update_service(
        self, service_id: str, body: ServiceUpdateServiceRequest
    ) -> None:
        """Update a service."""
        await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/service/{service_id}/",
            json=body.model_dump(mode="json", exclude_none=True),
        )

    async def upsert_version_set(
        self,
        service_id: str,
        version_set_name: str,
        body: ServiceUpsertServiceVersionSetRequest,
    ) -> None:
        """Upsert a service version set."""
        await self._http.request(
            "PUT",
            f"/v1/{self._organization_id}/service/{service_id}/version_sets/{version_set_name}/",
            json=body.model_dump(mode="json", exclude_none=True),
        )

    async def delete_version_set(self, service_id: str, version_set_name: str) -> None:
        """Delete a service version set."""
        await self._http.request(
            "DELETE",
            f"/v1/{self._organization_id}/service/{service_id}/version_sets/{version_set_name}/",
        )

    # --- Convenience aliases ---

    async def list(
        self, params: GetServicesParametersQuery | None = None
    ) -> ServiceGetServicesResponse:
        """Alias for get_services."""
        return await self.get_services(params)

    async def create(
        self, body: ServiceCreateServiceRequest
    ) -> ServiceCreateServiceResponse:
        """Alias for create_service."""
        return await self.create_service(body)


class ServiceResource:
    """Service resource (synchronous)."""

    def __init__(self, http_client: AmigoHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    def get_services(
        self, params: GetServicesParametersQuery | None = None
    ) -> ServiceGetServicesResponse:
        """List services for the organization."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/service/",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return ServiceGetServicesResponse.model_validate_json(response.text)

    def create_service(
        self, body: ServiceCreateServiceRequest
    ) -> ServiceCreateServiceResponse:
        """Create a new service."""
        response = self._http.request(
            "POST",
            f"/v1/{self._organization_id}/service/",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return ServiceCreateServiceResponse.model_validate_json(response.text)

    def update_service(
        self, service_id: str, body: ServiceUpdateServiceRequest
    ) -> None:
        """Update a service."""
        self._http.request(
            "POST",
            f"/v1/{self._organization_id}/service/{service_id}/",
            json=body.model_dump(mode="json", exclude_none=True),
        )

    def upsert_version_set(
        self,
        service_id: str,
        version_set_name: str,
        body: ServiceUpsertServiceVersionSetRequest,
    ) -> None:
        """Upsert a service version set."""
        self._http.request(
            "PUT",
            f"/v1/{self._organization_id}/service/{service_id}/version_sets/{version_set_name}/",
            json=body.model_dump(mode="json", exclude_none=True),
        )

    def delete_version_set(self, service_id: str, version_set_name: str) -> None:
        """Delete a service version set."""
        self._http.request(
            "DELETE",
            f"/v1/{self._organization_id}/service/{service_id}/version_sets/{version_set_name}/",
        )

    # --- Convenience aliases ---

    def list(
        self, params: GetServicesParametersQuery | None = None
    ) -> ServiceGetServicesResponse:
        """Alias for get_services."""
        return self.get_services(params)

    def create(self, body: ServiceCreateServiceRequest) -> ServiceCreateServiceResponse:
        """Alias for create_service."""
        return self.create_service(body)
