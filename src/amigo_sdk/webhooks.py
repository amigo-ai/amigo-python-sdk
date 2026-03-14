"""Webhook event types, parsing, and signature verification for the Amigo AI platform."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Literal, Union


# -- Event types ---------------------------------------------------------------

PostProcessingType = Literal[
    "generate-tasks",
    "generate-user-models",
    "extract-memories",
    "compute-metrics",
]


@dataclass(frozen=True)
class ConversationPostProcessingCompleteEvent:
    """Fired when async post-processing completes for a conversation."""

    type: Literal["conversation-post-processing-complete"]
    post_processing_type: PostProcessingType
    conversation_id: str
    org_id: str


WebhookEvent = Union[ConversationPostProcessingCompleteEvent]
"""Discriminated union of all webhook event types."""

WebhookEventType = Literal["conversation-post-processing-complete"]

_EVENT_CONSTRUCTORS: dict[str, type] = {
    "conversation-post-processing-complete": ConversationPostProcessingCompleteEvent,
}


# -- Signature verification ----------------------------------------------------


class WebhookVerificationError(Exception):
    """Raised when webhook signature verification fails."""


def verify_signature(body: str, timestamp: str, signature: str, secret: str) -> None:
    """Verify the HMAC-SHA256 signature of a webhook payload.

    The expected format is ``v1:{timestamp}:{body}`` signed with the
    webhook destination secret.

    Raises:
        WebhookVerificationError: If the signature does not match.
    """
    payload = f"v1:{timestamp}:{body}"
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise WebhookVerificationError("Signature verification failed")


# -- Event parsing -------------------------------------------------------------


def parse_webhook_event(
    payload: str | bytes,
    signature: str | None = None,
    timestamp: str | None = None,
    secret: str | None = None,
    max_age_ms: int = 300_000,
) -> WebhookEvent:
    """Parse and optionally verify a webhook event payload.

    If *signature*, *timestamp*, and *secret* are all provided the
    HMAC-SHA256 signature is verified and the timestamp freshness is
    checked before parsing.

    Args:
        payload: Raw request body.
        signature: Value of the ``x-amigo-request-signature`` header.
        timestamp: Value of the ``x-amigo-request-timestamp`` header (ms).
        secret: Webhook destination secret for verification.
        max_age_ms: Maximum acceptable event age in milliseconds (default 5 min).

    Returns:
        A typed webhook event dataclass.

    Raises:
        WebhookVerificationError: On signature mismatch, stale timestamp, or unknown event type.
    """
    body = payload if isinstance(payload, str) else payload.decode("utf-8")

    # Verify if all pieces present
    if signature and timestamp and secret:
        verify_signature(body, timestamp, signature, secret)
        try:
            event_time = int(timestamp)
        except ValueError as exc:
            raise WebhookVerificationError("Invalid timestamp") from exc
        age = int(time.time() * 1000) - event_time
        if age > max_age_ms:
            raise WebhookVerificationError(
                f"Webhook event is too old ({age}ms ago, max {max_age_ms}ms)"
            )

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise WebhookVerificationError("Invalid JSON payload") from exc

    if not isinstance(data, dict) or "type" not in data:
        raise WebhookVerificationError('Payload missing "type" field')

    event_type = data["type"]
    constructor = _EVENT_CONSTRUCTORS.get(event_type)
    if constructor is None:
        raise WebhookVerificationError(f"Unknown webhook event type: {event_type}")

    return constructor(**data)  # type: ignore[return-value]
