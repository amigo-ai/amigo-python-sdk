import datetime as dt
from email.utils import format_datetime

import pytest

from amigo_sdk._retry_utils import (
    DEFAULT_RETRYABLE_STATUS,
    compute_retry_delay_seconds,
    is_retryable_response,
    parse_retry_after_seconds,
)


@pytest.mark.unit
class TestRetryUtils:
    def test_parse_retry_after_seconds_numeric(self):
        assert parse_retry_after_seconds("1.5") == pytest.approx(1.5, rel=1e-3)

    def test_parse_retry_after_seconds_http_date(self):
        future_dt = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=2)
        http_date = format_datetime(future_dt)
        sec = parse_retry_after_seconds(http_date)
        assert sec is not None and sec >= 0

    def test_is_retryable_response_policy_get_and_post_429_with_header(self):
        methods = {"GET"}
        statuses = DEFAULT_RETRYABLE_STATUS
        assert is_retryable_response("GET", 500, {}, methods, statuses) is True
        assert (
            is_retryable_response("POST", 429, {"Retry-After": "1"}, methods, statuses)
            is True
        )
        assert is_retryable_response("POST", 429, {}, methods, statuses) is False

    def test_compute_retry_delay_honors_retry_after_and_clamps(self):
        d = compute_retry_delay_seconds(1, 0.25, 0.5, "5.0")
        assert d == 0.5
