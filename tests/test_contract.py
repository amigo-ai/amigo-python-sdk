"""
Contract tests that verify SDK resource methods match the live OpenAPI spec.
Run with: RUN_CONTRACT=true pytest tests/test_contract.py -v
"""

import os
import json
import pytest
import urllib.request

OPENAPI_URL = "https://api.amigo.ai/v1/openapi.json"

# Map of SDK resource methods to their expected OpenAPI operationIds
SDK_OPERATION_MAP = {
    # AsyncConversationResource / ConversationResource
    "conversations.create_conversation": ["create-conversation"],
    "conversations.interact_with_conversation": ["interact-with-conversation"],
    "conversations.get_conversations": ["get-conversations"],
    "conversations.get_conversation_messages": ["get-conversation-messages"],
    "conversations.finish_conversation": ["finish-conversation"],
    "conversations.recommend_responses_for_interaction": [
        "recommend-responses-for-interaction"
    ],
    "conversations.get_interaction_insights": ["get-interaction-insights"],
    "conversations.get_message_source": ["get-message-source"],
    "conversations.generate_conversation_starters": ["generate-conversation-starters"],
    # AsyncUserResource / UserResource
    "users.get_users": ["get-users"],
    "users.create_user": ["create-user"],
    "users.delete_user": ["delete-user"],
    "users.update_user": ["modify-user"],
    "users.get_user_model": ["get-user-model"],
    # AsyncOrganizationResource / OrganizationResource
    "organizations.get_organization": ["get-organization"],
    # AsyncServiceResource / ServiceResource
    "services.get_services": ["get-services"],
}

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_CONTRACT"), reason="Set RUN_CONTRACT=true to run"
)


@pytest.fixture(scope="module")
def openapi_spec():
    """Fetch the live OpenAPI spec."""
    req = urllib.request.Request(OPENAPI_URL)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _extract_operation_ids(spec: dict) -> set[str]:
    """Extract all operationIds from the OpenAPI spec."""
    op_ids = set()
    for _path, methods in spec.get("paths", {}).items():
        for _method, operation in methods.items():
            if isinstance(operation, dict) and "operationId" in operation:
                op_ids.add(operation["operationId"])
    return op_ids


class TestOpenAPIContract:
    def test_spec_has_version(self, openapi_spec):
        assert openapi_spec["info"]["version"]

    def test_all_sdk_operations_exist_in_spec(self, openapi_spec):
        spec_ops = _extract_operation_ids(openapi_spec)
        missing = []

        for sdk_method, expected_ops in SDK_OPERATION_MAP.items():
            for op_id in expected_ops:
                if op_id not in spec_ops:
                    missing.append(f"{sdk_method} → {op_id}")

        assert missing == [], f"Operations missing from OpenAPI spec: {missing}"

    def test_no_excessive_unmapped_endpoints(self, openapi_spec):
        known_ops = set()
        for ops in SDK_OPERATION_MAP.values():
            known_ops.update(ops)

        spec_ops = _extract_operation_ids(openapi_spec)
        unmapped = spec_ops - known_ops

        if unmapped:
            print(f"\n{len(unmapped)} endpoints in spec not mapped in SDK:")
            for op in sorted(unmapped)[:10]:
                print(f"  - {op}")

        # Informational — fail only on unreasonable drift
        assert len(unmapped) < 100, f"Too many unmapped endpoints: {len(unmapped)}"
