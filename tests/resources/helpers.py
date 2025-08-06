"""Shared test helpers for resource tests."""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from src.generated.model import (
    ServiceInstance,
    SrcAppEndpointsOrganizationGetOrganizationResponse,
    SrcAppEndpointsServiceGetServicesResponse,
)


@asynccontextmanager
async def mock_http_request(mock_response_data, status_code=200):
    """
    Context manager that mocks HTTP requests with auth token handling.

    Args:
        mock_response_data: The data to return in the response (can be JSON string or Pydantic object)
        status_code: HTTP status code to return (default: 200)
    """
    # Create mock response
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.is_success = status_code < 400

    # Convert Pydantic objects to JSON strings for response.text
    if hasattr(mock_response_data, "model_dump_json"):
        # It's a Pydantic object, convert to JSON
        mock_response.text = mock_response_data.model_dump_json()
    else:
        # It's already a string
        mock_response.text = mock_response_data

    # Create fresh auth token
    fresh_token = Mock(
        id_token="test-bearer-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    def mock_request(*args, **kwargs):
        return mock_response

    with (
        patch("src.http_client.sign_in_with_api_key", return_value=fresh_token),
        patch("httpx.AsyncClient.request", return_value=mock_response),
    ):
        yield mock_response


def create_organization_response_data() -> (
    SrcAppEndpointsOrganizationGetOrganizationResponse
):
    """Create mock data matching SrcAppEndpointsOrganizationGetOrganizationResponse schema."""
    return SrcAppEndpointsOrganizationGetOrganizationResponse(
        org_id="test-org-123",
        org_name="Test Organization",
        title="Your AI Assistant Platform",
        main_description="Build and deploy AI assistants for your organization",
        sub_description="Streamline workflows with intelligent automation",
        onboarding_instructions=[
            "Welcome to our platform!",
            "Let's get you started with your first assistant.",
        ],
        default_user_preferences=None,
    )


def create_services_response_data() -> SrcAppEndpointsServiceGetServicesResponse:
    """Create mock data matching SrcAppEndpointsServiceGetServicesResponse schema."""
    return SrcAppEndpointsServiceGetServicesResponse(
        services=[
            ServiceInstance(
                id="service-1",
                name="Customer Support Bot",
                description="AI assistant for customer inquiries",
                version_sets={},
                is_active=True,
                service_hierarchical_state_machine_id="hsm-1",
                agent_id="agent-1",
                tags=[
                    {"key": "support", "value": "customer-support"},
                    {"key": "customer", "value": "external"},
                ],
            ),
            ServiceInstance(
                id="service-2",
                name="Sales Assistant",
                description="AI assistant for sales support",
                version_sets={},
                is_active=True,
                service_hierarchical_state_machine_id="hsm-2",
                agent_id="agent-2",
                tags=[{"key": "sales", "value": "internal"}],
            ),
        ],
        has_more=False,
        continuation_token=None,
        filter_values=None,
    )
