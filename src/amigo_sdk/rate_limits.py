"""Rate limit metadata parsed from Amigo API response headers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping


@dataclass(frozen=True)
class RateLimitInfo:
    """Rate limit state from HTTP response headers.

    Headers: ``X-RateLimit-Limit``, ``X-RateLimit-Remaining``, ``X-RateLimit-Reset``
    """

    limit: int
    """Maximum requests allowed in the current window."""
    remaining: int
    """Requests remaining in the current window."""
    reset: datetime
    """When the current rate-limit window resets (UTC)."""


def parse_rate_limit_headers(
    headers: Mapping[str, str],
) -> RateLimitInfo | None:
    """Parse rate limit info from HTTP response headers.

    Returns ``None`` if the required headers are not present.
    """
    limit = headers.get("x-ratelimit-limit")
    remaining = headers.get("x-ratelimit-remaining")
    reset = headers.get("x-ratelimit-reset")

    if limit is None or remaining is None or reset is None:
        return None

    try:
        limit_int = int(limit)
        remaining_int = int(remaining)
        reset_epoch = int(reset)
    except ValueError:
        return None

    return RateLimitInfo(
        limit=limit_int,
        remaining=remaining_int,
        reset=datetime.fromtimestamp(reset_epoch, tz=timezone.utc),
    )


RateLimitCallback = Callable[[RateLimitInfo, str], None]
"""Callback invoked after each API response with rate limit info."""
