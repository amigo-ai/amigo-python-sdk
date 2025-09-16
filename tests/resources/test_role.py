import pytest

from amigo_sdk.config import AmigoConfig
from amigo_sdk.errors import ValidationError
from amigo_sdk.generated.model import (
    FrontendView,
    PermissionGrantInput,
    PermissionGrantInputAction,
    PermissionGrantOutput,
    RoleCreateRoleRequest,
    RoleCreateRoleResponse,
    RoleGetRolesResponse,
)
from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient
from amigo_sdk.resources.role import AsyncRoleResource, RoleResource

from .helpers import (
    create_role_response_data,
    mock_http_request,
    mock_http_request_sync,
)


@pytest.fixture
def mock_config():
    return AmigoConfig(
        api_key="test-api-key",
        api_key_id="test-api-key-id",
        user_id="test-user-id",
        organization_id="test-org-123",
        base_url="https://api.example.com",
    )


@pytest.fixture
def mock_role_request_body() -> RoleCreateRoleRequest:
    return RoleCreateRoleRequest(
        role_name="role_name",
        description="description",
        permission_grants=[
            PermissionGrantInput(
                action=PermissionGrantInputAction.allow,
                permission_name="permission_name",
                conditions={},
                description=None,
            )
        ],
        frontend_view=FrontendView.admin,
        is_base_role=True,
        inherited_from=None,
    )


@pytest.fixture
def role_resource(mock_config) -> AsyncRoleResource:
    http_client = AmigoAsyncHttpClient(mock_config)
    return AsyncRoleResource(http_client, "test-org-123")


@pytest.mark.unit
class TestRoleResource:
    """Simple test suite for the Role Resource."""

    @pytest.mark.asyncio
    async def test_get_roles_returns_expected_data(
        self, role_resource: AsyncRoleResource
    ):
        mock_data = create_role_response_data()
        async with mock_http_request(mock_data):
            result = await role_resource.get_roles()
            assert isinstance(result, RoleGetRolesResponse)
            roleInstance = result.roles[0]
            assert roleInstance.id == "role-1"
            assert roleInstance.name == "role-name"
            assert roleInstance.description == "role-description"
            assert roleInstance.frontend_view == FrontendView.client
            assert isinstance(roleInstance.permission_grants[0], PermissionGrantOutput)
            assert roleInstance.inherited_from == "role-inherited_from"
            assert roleInstance.is_base_role
            grant = roleInstance.permission_grants[0]
            assert grant.action == PermissionGrantInputAction.allow
            assert grant.conditions == {}
            assert grant.permission_name == "role-permission_name"
            assert grant.description == "role-permission-description"

    @pytest.mark.asyncio
    async def test_create_role_sends_body_and_returns_response(
        self, role_resource, mock_role_request_body
    ):
        mock_response = RoleCreateRoleResponse(role_id="role_id")
        async with mock_http_request(mock_response):
            result = await role_resource.create_role(mock_role_request_body)
            assert isinstance(result, RoleCreateRoleResponse)
            assert result.role_id == "role_id"

    @pytest.mark.asyncio
    async def test_create_role_validation_error_raises(
        self, role_resource, mock_role_request_body
    ):
        async with mock_http_request({"detail": "bad"}, status_code=422):
            with pytest.raises(ValidationError):
                await role_resource.create_role(mock_role_request_body)


@pytest.mark.unit
class TestRoleResourceSync:
    """Sync RoleResource tests mirroring async coverage."""

    def _resource(self, mock_config) -> RoleResource:
        http = AmigoHttpClient(mock_config)
        return RoleResource(http, mock_config.organization_id)

    def test_get_roles_returns_expected_data_sync(self, mock_config):
        res = self._resource(mock_config)
        mock_data = create_role_response_data()
        with mock_http_request_sync(mock_data):
            result = res.get_roles()
            assert isinstance(result, RoleGetRolesResponse)
            roleInstance = result.roles[0]
            assert roleInstance.id == "role-1"
            assert roleInstance.name == "role-name"
            assert roleInstance.description == "role-description"
            assert roleInstance.frontend_view == FrontendView.client
            assert isinstance(roleInstance.permission_grants[0], PermissionGrantOutput)
            assert roleInstance.inherited_from == "role-inherited_from"
            assert roleInstance.is_base_role
            grant = roleInstance.permission_grants[0]
            assert grant.action == PermissionGrantInputAction.allow
            assert grant.conditions == {}
            assert grant.permission_name == "role-permission_name"
            assert grant.description == "role-permission-description"

    def test_create_role_sends_body_and_returns_response_sync(
        self, mock_config, mock_role_request_body
    ):
        res = self._resource(mock_config)
        mock_response = RoleCreateRoleResponse(role_id="role_id")
        with mock_http_request_sync(mock_response):
            result = res.create_role(mock_role_request_body)
            assert isinstance(result, RoleCreateRoleResponse)
            assert result.role_id == "role_id"

    def test_create_role_validation_error_raises(
        self, mock_config, mock_role_request_body
    ):
        res = self._resource(mock_config)
        with mock_http_request_sync({"detail": "bad"}, status_code=422):
            with pytest.raises(ValidationError):
                res.create_role(mock_role_request_body)
