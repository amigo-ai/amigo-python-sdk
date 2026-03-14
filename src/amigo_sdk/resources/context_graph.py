from amigo_sdk.generated.model import (
    CreateServiceHierarchicalStateMachineVersionParametersQuery,
    GetServiceHierarchicalStateMachinesParametersQuery,
    GetServiceHierarchicalStateMachineVersionsParametersQuery,
    OrganizationCreateServiceHierarchicalStateMachineRequest,
    OrganizationCreateServiceHierarchicalStateMachineResponse,
    OrganizationCreateServiceHierarchicalStateMachineVersionRequest,
    OrganizationCreateServiceHierarchicalStateMachineVersionResponse,
    OrganizationGetServiceHierarchicalStateMachinesResponse,
    OrganizationGetServiceHierarchicalStateMachineVersionsResponse,
)
from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient


class AsyncContextGraphResource:
    """Context graph (HSM) resource for Amigo API operations."""

    def __init__(self, http_client: AmigoAsyncHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    async def create_context_graph(
        self, body: OrganizationCreateServiceHierarchicalStateMachineRequest
    ) -> OrganizationCreateServiceHierarchicalStateMachineResponse:
        """Create a new context graph."""
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return OrganizationCreateServiceHierarchicalStateMachineResponse.model_validate_json(
            response.text
        )

    async def get_context_graphs(
        self,
        params: GetServiceHierarchicalStateMachinesParametersQuery | None = None,
    ) -> OrganizationGetServiceHierarchicalStateMachinesResponse:
        """List context graphs for the organization."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return (
            OrganizationGetServiceHierarchicalStateMachinesResponse.model_validate_json(
                response.text
            )
        )

    async def create_context_graph_version(
        self,
        context_graph_id: str,
        body: OrganizationCreateServiceHierarchicalStateMachineVersionRequest,
        params: CreateServiceHierarchicalStateMachineVersionParametersQuery
        | None = None,
    ) -> OrganizationCreateServiceHierarchicalStateMachineVersionResponse:
        """Create a new version of a context graph."""
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine/{context_graph_id}/",
            json=body.model_dump(mode="json", exclude_none=True),
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return OrganizationCreateServiceHierarchicalStateMachineVersionResponse.model_validate_json(
            response.text
        )

    async def delete_context_graph(self, context_graph_id: str) -> None:
        """Delete a context graph."""
        await self._http.request(
            "DELETE",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine/{context_graph_id}/",
        )

    async def get_context_graph_versions(
        self,
        context_graph_id: str,
        params: GetServiceHierarchicalStateMachineVersionsParametersQuery | None = None,
    ) -> OrganizationGetServiceHierarchicalStateMachineVersionsResponse:
        """Get versions of a context graph."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine/{context_graph_id}/version",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return OrganizationGetServiceHierarchicalStateMachineVersionsResponse.model_validate_json(
            response.text
        )

    # --- Convenience aliases ---

    async def list(
        self,
        params: GetServiceHierarchicalStateMachinesParametersQuery | None = None,
    ) -> OrganizationGetServiceHierarchicalStateMachinesResponse:
        """Alias for get_context_graphs."""
        return await self.get_context_graphs(params)

    async def create(
        self, body: OrganizationCreateServiceHierarchicalStateMachineRequest
    ) -> OrganizationCreateServiceHierarchicalStateMachineResponse:
        """Alias for create_context_graph."""
        return await self.create_context_graph(body)

    async def delete(self, context_graph_id: str) -> None:
        """Alias for delete_context_graph."""
        return await self.delete_context_graph(context_graph_id)


class ContextGraphResource:
    """Context graph (HSM) resource (synchronous)."""

    def __init__(self, http_client: AmigoHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    def create_context_graph(
        self, body: OrganizationCreateServiceHierarchicalStateMachineRequest
    ) -> OrganizationCreateServiceHierarchicalStateMachineResponse:
        """Create a new context graph."""
        response = self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return OrganizationCreateServiceHierarchicalStateMachineResponse.model_validate_json(
            response.text
        )

    def get_context_graphs(
        self,
        params: GetServiceHierarchicalStateMachinesParametersQuery | None = None,
    ) -> OrganizationGetServiceHierarchicalStateMachinesResponse:
        """List context graphs for the organization."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return (
            OrganizationGetServiceHierarchicalStateMachinesResponse.model_validate_json(
                response.text
            )
        )

    def create_context_graph_version(
        self,
        context_graph_id: str,
        body: OrganizationCreateServiceHierarchicalStateMachineVersionRequest,
        params: CreateServiceHierarchicalStateMachineVersionParametersQuery
        | None = None,
    ) -> OrganizationCreateServiceHierarchicalStateMachineVersionResponse:
        """Create a new version of a context graph."""
        response = self._http.request(
            "POST",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine/{context_graph_id}/",
            json=body.model_dump(mode="json", exclude_none=True),
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return OrganizationCreateServiceHierarchicalStateMachineVersionResponse.model_validate_json(
            response.text
        )

    def delete_context_graph(self, context_graph_id: str) -> None:
        """Delete a context graph."""
        self._http.request(
            "DELETE",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine/{context_graph_id}/",
        )

    def get_context_graph_versions(
        self,
        context_graph_id: str,
        params: GetServiceHierarchicalStateMachineVersionsParametersQuery | None = None,
    ) -> OrganizationGetServiceHierarchicalStateMachineVersionsResponse:
        """Get versions of a context graph."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/organization/service_hierarchical_state_machine/{context_graph_id}/version",
            params=params.model_dump(mode="json", exclude_none=True)
            if params
            else None,
        )
        return OrganizationGetServiceHierarchicalStateMachineVersionsResponse.model_validate_json(
            response.text
        )

    # --- Convenience aliases ---

    def list(
        self,
        params: GetServiceHierarchicalStateMachinesParametersQuery | None = None,
    ) -> OrganizationGetServiceHierarchicalStateMachinesResponse:
        """Alias for get_context_graphs."""
        return self.get_context_graphs(params)

    def create(
        self, body: OrganizationCreateServiceHierarchicalStateMachineRequest
    ) -> OrganizationCreateServiceHierarchicalStateMachineResponse:
        """Alias for create_context_graph."""
        return self.create_context_graph(body)

    def delete(self, context_graph_id: str) -> None:
        """Alias for delete_context_graph."""
        return self.delete_context_graph(context_graph_id)
