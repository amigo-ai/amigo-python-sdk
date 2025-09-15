from amigo_sdk.generated.model import (
    RoleGetRolesResponse,
    RoleCreateRoleRequest,
    RoleCreateRoleResponse
)

from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient

class AsyncRoleResource:
    """Role resource for Amigo API operations."""
    def __init__(self, http_client: AmigoAsyncHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id
    
    async def get_roles(self) -> RoleGetRolesResponse:
        response = await self._http.request(
            "GET", f"/v1/{self._organization_id}/role/"
        )

        return RoleGetRolesResponse.model_validate_json(response.text)

    async def create_role(
        self, body: RoleCreateRoleRequest
    ) -> RoleCreateRoleResponse:
        """Create a new role to the organization."""
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/role/",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return RoleCreateRoleResponse.model_validate_json(response.text)

class RoleResource:
    def __init__(self, http_client: AmigoHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id
    
    def get_roles(self) -> RoleGetRolesResponse:
        response = self._http.request(
            "GET", f"/v1/{self._organization_id}/role/"
        )

        return RoleGetRolesResponse.model_validate_json(response.text)

    def create_role(
        self, body: RoleCreateRoleRequest
    ) -> RoleCreateRoleResponse:
        response = self._http.request(
            "POST",
            f"/v1/{self._organization_id}/role/",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return RoleCreateRoleResponse.model_validate_json(response.text)