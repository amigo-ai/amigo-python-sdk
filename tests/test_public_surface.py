import hashlib
import hmac
import json
import time
from datetime import UTC, datetime

import pytest

from amigo_sdk import models
from amigo_sdk.generated.model import OrganizationGetOrganizationResponse
from amigo_sdk.rate_limits import RateLimitInfo, parse_rate_limit_headers
from amigo_sdk.webhooks import (
    ConversationPostProcessingCompleteEvent,
    WebhookVerificationError,
    parse_webhook_event,
    verify_signature,
)


@pytest.mark.unit
def test_models_module_reexports_public_types() -> None:
    assert "OrganizationGetOrganizationResponse" in models.__all__
    assert models.OrganizationGetOrganizationResponse is OrganizationGetOrganizationResponse


@pytest.mark.unit
def test_parse_rate_limit_headers_returns_structured_info() -> None:
    result = parse_rate_limit_headers(
        {
            "x-ratelimit-limit": "100",
            "x-ratelimit-remaining": "42",
            "x-ratelimit-reset": "1735689600",
        }
    )

    assert result == RateLimitInfo(
        limit=100,
        remaining=42,
        reset=datetime.fromtimestamp(1735689600, tz=UTC),
    )


@pytest.mark.unit
def test_parse_rate_limit_headers_returns_none_for_invalid_headers() -> None:
    assert parse_rate_limit_headers({"x-ratelimit-limit": "abc"}) is None


@pytest.mark.unit
def test_verify_signature_accepts_valid_signature() -> None:
    body = '{"type":"conversation-post-processing-complete"}'
    timestamp = "1735689600000"
    secret = "test-secret"
    signature = hmac.new(
        secret.encode(),
        f"v1:{timestamp}:{body}".encode(),
        hashlib.sha256,
    ).hexdigest()

    verify_signature(body, timestamp, signature, secret)


@pytest.mark.unit
def test_parse_webhook_event_parses_signed_payload() -> None:
    payload = json.dumps(
        {
            "type": "conversation-post-processing-complete",
            "post_processing_type": "generate-tasks",
            "conversation_id": "conv-123",
            "org_id": "org-123",
        }
    )
    timestamp = str(int(time.time() * 1000))
    secret = "test-secret"
    signature = hmac.new(
        secret.encode(),
        f"v1:{timestamp}:{payload}".encode(),
        hashlib.sha256,
    ).hexdigest()

    event = parse_webhook_event(
        payload,
        signature=signature,
        timestamp=timestamp,
        secret=secret,
    )

    assert isinstance(event, ConversationPostProcessingCompleteEvent)
    assert event.org_id == "org-123"


@pytest.mark.unit
def test_parse_webhook_event_rejects_unknown_event_type() -> None:
    payload = json.dumps({"type": "unknown-event"})

    with pytest.raises(WebhookVerificationError, match="Unknown webhook event type"):
        parse_webhook_event(payload)
