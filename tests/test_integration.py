import os
from uuid import uuid4

import pytest

from src.config import AmigoConfig
from src.errors import AuthenticationError
from src.generated.model import (
    IdentityInput,
    OrganizationCreateAgentRequest,
    OrganizationCreateAgentResponse,
    OrganizationCreateAgentVersionRequest,
    OrganizationCreateAgentVersionResponse,
    OrganizationGetOrganizationResponse,
    RelationshipToDeveloperInput,
    ServiceGetServicesResponse,
    VoiceConfigInput,
)
from src.sdk_client import AmigoClient


# Function-scoped fixture to create and clean up an agent per test
@pytest.fixture
async def agent_id():
    async with AmigoClient() as client:
        unique_name = f"sdk_test_agent_{uuid4().hex[:8]}"
        agent = await client.organization.create_agent(
            body=OrganizationCreateAgentRequest(agent_name=unique_name),
        )
        try:
            yield agent.id
        finally:
            try:
                await client.organization.delete_agent(agent_id=agent.id)
            except Exception:
                # Best-effort cleanup; ignore if already deleted
                pass


@pytest.mark.integration
class TestOrganizationIntegration:
    agent_id: str | None = None
    """Integration tests for Amigo API.

    These tests make actual API calls to the Amigo service.
    Required environment variables: AMIGO_API_KEY, AMIGO_API_KEY_ID,
    AMIGO_USER_ID, AMIGO_ORGANIZATION_ID, AMIGO_BASE_URL (optional).

    Create a .env file in the project root or set environment variables directly.
    Tests will fail if required variables are missing.
    """

    @pytest.fixture
    def required_env_vars(self):
        """Check that required environment variables are set."""
        required_vars = [
            "AMIGO_API_KEY",
            "AMIGO_API_KEY_ID",
            "AMIGO_USER_ID",
            "AMIGO_ORGANIZATION_ID",
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            pytest.fail(
                f"Integration tests require environment variables to be set.\n"
                f"Missing: {', '.join(missing_vars)}\n\n"
                f"Please set these environment variables or create a .env file in the project root:\n"
                f"AMIGO_API_KEY=your-api-key\n"
                f"AMIGO_API_KEY_ID=your-api-key-id\n"
                f"AMIGO_USER_ID=your-user-id\n"
                f"AMIGO_ORGANIZATION_ID=your-organization-id\n"
                f"AMIGO_BASE_URL=https://your-api-base-url (optional)"
            )

        return {var: os.getenv(var) for var in required_vars}

    async def test_get_services(self):
        """Test getting services."""
        async with AmigoClient() as client:
            services = await client.service.get_services()

            assert services is not None
            assert isinstance(services, ServiceGetServicesResponse)

    async def test_get_organization(self):
        """Test getting organization details using environment variables for config."""

        # Create client using environment variables
        async with AmigoClient() as client:
            # Get organization details
            organization = await client.organization.get()

            # Verify we got a valid response
            assert organization is not None

            # Verify response is the correct pydantic model type
            assert isinstance(organization, OrganizationGetOrganizationResponse)

            # Verify model can serialize (proves it's valid)
            assert organization.model_dump_json() is not None

            # Verify organization has a title field
            assert hasattr(organization, "title"), (
                "Organization should have a title field"
            )
            assert organization.title is not None, (
                "Organization title should not be None"
            )

    async def test_create_agent(self):
        """Test creating an agent."""
        async with AmigoClient() as client:
            unique_name = f"sdk_test_agent_{uuid4().hex[:8]}"
            agent = None
            try:
                agent = await client.organization.create_agent(
                    body=OrganizationCreateAgentRequest(agent_name=unique_name),
                )
                print(agent)
                assert agent is not None
                assert isinstance(agent, OrganizationCreateAgentResponse)
            finally:
                try:
                    if agent and getattr(agent, "id", None):
                        await client.organization.delete_agent(agent_id=agent.id)
                except Exception:
                    # Best-effort cleanup; ignore if deletion fails
                    pass

            # Creation verified by type/instance assertions above

    async def test_create_agent_version(self, agent_id):
        """Test creating an agent version."""
        async with AmigoClient() as client:
            agent_version = await client.organization.create_agent_version(
                agent_id=agent_id,
                body=OrganizationCreateAgentVersionRequest(
                    initials="SDK",
                    identity=IdentityInput(
                        name="sdk_integration_test_agent",
                        role="sdk_integration_test_role",
                        developed_by="SDK Integration Tests",
                        default_spoken_language="eng",
                        relationship_to_developer=RelationshipToDeveloperInput(
                            ownership="user",
                            type="assistant",
                            conversation_visibility="visible",
                            thought_visibility="hidden",
                        ),
                    ),
                    background="SDK integration test background",
                    behaviors=[],
                    communication_patterns=[],
                    voice_config=VoiceConfigInput(
                        voice_id="iP95p4xoKVk53GoZ742B",
                        stability=0.35,
                        similarity_boost=0.9,
                        style=0,
                    ),
                ),
            )
            print(agent_version)
            assert agent_version is not None
            assert isinstance(agent_version, OrganizationCreateAgentVersionResponse)

    async def test_delete_agent(self, agent_id):
        """Test deleting an agent."""
        async with AmigoClient() as client:
            await client.organization.delete_agent(agent_id=agent_id)

    async def test_invalid_credentials_raises_authentication_error(self):
        """Test that invalid credentials raise appropriate authentication errors."""

        # Fail if we don't have valid credentials to test with
        if not os.getenv("AMIGO_API_KEY"):
            pytest.fail(
                "Cannot test authentication error handling without valid credentials.\n"
                "Please set AMIGO_API_KEY environment variable."
            )

        # Create client with invalid API key
        with pytest.raises(AuthenticationError):
            async with AmigoClient(
                api_key="invalid_key",
            ) as client:
                await client.organization.get()

    async def test_client_config_property(self, required_env_vars):
        """Test that the client config property works correctly."""

        async with AmigoClient() as client:
            config = client.config

            # Verify config contains expected values
            assert config.api_key == required_env_vars["AMIGO_API_KEY"]
            assert config.api_key_id == required_env_vars["AMIGO_API_KEY_ID"]
            assert config.user_id == required_env_vars["AMIGO_USER_ID"]
            assert config.organization_id == required_env_vars["AMIGO_ORGANIZATION_ID"]
            assert config.base_url == os.getenv(
                "AMIGO_BASE_URL", "https://api.amigo.ai"
            )

    def test_config_creation(self, required_env_vars):
        """Test that AmigoConfig can be created from environment variables."""
        # This should work now with the fixed field aliases
        config = AmigoConfig()

        # Verify config contains expected values
        assert config.api_key == required_env_vars["AMIGO_API_KEY"]
        assert config.api_key_id == required_env_vars["AMIGO_API_KEY_ID"]
        assert config.user_id == required_env_vars["AMIGO_USER_ID"]
        assert config.organization_id == required_env_vars["AMIGO_ORGANIZATION_ID"]
