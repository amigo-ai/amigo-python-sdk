import os

import pytest

from amigo_sdk import errors
from amigo_sdk.generated.model import (
    GetUsersParametersQuery,
    UserCreateInvitedUserRequest,
    UserUpdateUserInfoRequest,
)
from amigo_sdk.sdk_client import AmigoClient, AsyncAmigoClient

print("AMIGO_API_KEY_ID:", os.environ.get("AMIGO_API_KEY_ID"))
print("AMIGO_ORGANIZATION_ID:", os.environ.get("AMIGO_ORGANIZATION_ID"))
print("AMIGO_USER_ID:", os.environ.get("AMIGO_USER_ID"))
print("AMIGO_BASE_URL:", os.environ.get("AMIGO_BASE_URL"))


@pytest.mark.integration
class TestUserIntegration:
    created_user_id: str | None = None
    created_user_email: str | None = None

    async def test_create_user(self):
        async with AsyncAmigoClient() as client:
            unique_suffix = str(os.getpid()) + "-" + str(int(os.times().elapsed * 1000))
            email = f"py-sdk-it-{unique_suffix}@example.com"
            body = UserCreateInvitedUserRequest(
                first_name="PY",
                last_name="SDK-IT",
                email=email,
                role_name="DefaultUserRole",
            )

            result = await client.users.create_user(body)
            assert result is not None
            assert isinstance(result.user_id, str)
            type(self).created_user_id = result.user_id
            type(self).created_user_email = email

    async def test_update_user(self):
        assert type(self).created_user_id is not None
        async with AsyncAmigoClient() as client:
            body = UserUpdateUserInfoRequest(
                first_name="PY-Updated",
                last_name="SDK-IT-Updated",
                preferred_language={},
                timezone={},
            )
            await client.users.update_user(type(self).created_user_id, body)

    async def test_get_users_filters(self):
        assert type(self).created_user_id is not None
        assert type(self).created_user_email is not None
        async with AsyncAmigoClient() as client:
            by_id = await client.users.get_users(
                GetUsersParametersQuery(user_id=[type(self).created_user_id])
            )
            assert by_id is not None
            assert any(u.user_id == type(self).created_user_id for u in by_id.users)

            by_email = await client.users.get_users(
                GetUsersParametersQuery(email=[type(self).created_user_email])
            )
            assert by_email is not None
            assert any(u.email == type(self).created_user_email for u in by_email.users)

    # we need to get the user model for the authenticated user because the permission grant for the user model
    # does not allow access to non-admin user user models
    async def test_get_user_model(self):
        user_id = os.environ.get("AMIGO_USER_ID")
        assert user_id is not None, "AMIGO_USER_ID environment variable must be set"
        async with AsyncAmigoClient() as client:
            result = await client.users.get_user_model(user_id)
            assert result is not None
            assert isinstance(result.user_models, list)
            assert isinstance(result.additional_context, list)

    async def test_delete_user(self):
        assert type(self).created_user_id is not None
        async with AsyncAmigoClient() as client:
            await client.users.delete_user(type(self).created_user_id)

    async def test_error_cases(self):
        async with AsyncAmigoClient() as client:
            # Create with bad role
            body = UserCreateInvitedUserRequest(
                first_name="Bad",
                last_name="Role",
                email=f"bad-role-{os.getpid()}@example.com",
                role_name="role-that-does-not-exist",
            )
            with pytest.raises(errors.NotFoundError):
                await client.users.create_user(body)

            # Update non-existent user
            upd = UserUpdateUserInfoRequest(
                first_name="X",
                last_name="Y",
                preferred_language=None,
                timezone=None,
            )
            with pytest.raises(errors.NotFoundError):
                await client.users.update_user("non-existent-id", upd)

            # Get users for invalid org triggers auth at token exchange → AuthenticationError
            async with AsyncAmigoClient(
                organization_id="invalid-org-id-123"
            ) as bad_client:
                with pytest.raises(errors.AuthenticationError):
                    await bad_client.users.get_users()

            # Get user model for non-existent user
            with pytest.raises(errors.NotFoundError):
                await client.users.get_user_model("non-existent-id")

            # Delete non-existent user
            with pytest.raises(errors.NotFoundError):
                await client.users.delete_user("non-existent-id")


@pytest.mark.integration
class TestUserIntegrationSync:
    created_user_id: str | None = None
    created_user_email: str | None = None

    def test_create_user(self):
        with AmigoClient() as client:
            unique_suffix = str(os.getpid()) + "-" + str(int(os.times().elapsed * 1000))
            email = f"py-sdk-it-{unique_suffix}@example.com"
            body = UserCreateInvitedUserRequest(
                first_name="PY",
                last_name="SDK-IT",
                email=email,
                role_name="DefaultUserRole",
            )

            result = client.users.create_user(body)
            assert result is not None
            assert isinstance(result.user_id, str)
            type(self).created_user_id = result.user_id
            type(self).created_user_email = email

    def test_update_user(self):
        assert type(self).created_user_id is not None
        with AmigoClient() as client:
            body = UserUpdateUserInfoRequest(
                first_name="PY-Updated",
                last_name="SDK-IT-Updated",
                preferred_language={},
                timezone={},
            )
            client.users.update_user(type(self).created_user_id, body)

    def test_get_users_filters(self):
        assert type(self).created_user_id is not None
        assert type(self).created_user_email is not None
        with AmigoClient() as client:
            by_id = client.users.get_users(
                GetUsersParametersQuery(user_id=[type(self).created_user_id])
            )
            assert by_id is not None
            assert any(u.user_id == type(self).created_user_id for u in by_id.users)

            by_email = client.users.get_users(
                GetUsersParametersQuery(email=[type(self).created_user_email])
            )
            assert by_email is not None
            assert any(u.email == type(self).created_user_email for u in by_email.users)

    def test_get_user_model(self):
        user_id = os.environ.get("AMIGO_USER_ID")
        assert user_id is not None, "AMIGO_USER_ID environment variable not set"
        with AmigoClient() as client:
            result = client.users.get_user_model(user_id)
            assert result is not None
            assert isinstance(result.user_models, list)
            assert isinstance(result.additional_context, list)

    def test_delete_user(self):
        assert type(self).created_user_id is not None
        with AmigoClient() as client:
            client.users.delete_user(type(self).created_user_id)

    def test_error_cases(self):
        with AmigoClient() as client:
            body = UserCreateInvitedUserRequest(
                first_name="Bad",
                last_name="Role",
                email=f"bad-role-{os.getpid()}@example.com",
                role_name="role-that-does-not-exist",
            )
            with pytest.raises(errors.NotFoundError):
                client.users.create_user(body)

            upd = UserUpdateUserInfoRequest(
                first_name="X",
                last_name="Y",
                preferred_language=None,
                timezone=None,
            )
            with pytest.raises(errors.NotFoundError):
                client.users.update_user("non-existent-id", upd)

            with AmigoClient(organization_id="invalid-org-id-123") as bad_client:
                with pytest.raises(errors.AuthenticationError):
                    bad_client.users.get_users()

            with pytest.raises(errors.NotFoundError):
                client.users.get_user_model("non-existent-id")

            with pytest.raises(errors.NotFoundError):
                client.users.delete_user("non-existent-id")
