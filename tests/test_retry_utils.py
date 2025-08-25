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
    # parse_retry_after_seconds
    def test_parse_retry_after_seconds_numeric(self):
        assert parse_retry_after_seconds("1.5") == pytest.approx(1.5, rel=1e-3)

    def test_parse_retry_after_seconds_negative_numeric_clamped(self):
        assert parse_retry_after_seconds("-3") == 0.0

    def test_parse_retry_after_seconds_empty_and_none(self):
        assert parse_retry_after_seconds("") is None
        assert parse_retry_after_seconds(None) is None  # type: ignore[arg-type]

    def test_parse_retry_after_seconds_invalid_string(self):
        # Invalid string should return None (parser returns None)
        assert parse_retry_after_seconds("not-a-number") is None

    def test_parse_retry_after_seconds_http_date_future_and_past(self):
        future_dt = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=2)
        http_date_future = format_datetime(future_dt)
        sec_future = parse_retry_after_seconds(http_date_future)
        assert sec_future is not None and sec_future >= 0

        past_dt = dt.datetime.now(dt.UTC) - dt.timedelta(seconds=10)
        http_date_past = format_datetime(past_dt)
        sec_past = parse_retry_after_seconds(http_date_past)
        assert sec_past == 0.0

    def test_parse_retry_after_seconds_http_date_tz_naive_is_normalized(self):
        # Create an HTTP-date string without timezone; parser returns naive dt
        future_naive = dt.datetime.utcnow() + dt.timedelta(seconds=1)
        http_date_naive = future_naive.strftime("%a, %d %b %Y %H:%M:%S")
        sec = parse_retry_after_seconds(http_date_naive)
        assert sec is not None and sec >= 0.0

    def test_parse_retry_after_seconds_parser_exception_returns_none(self, monkeypatch):
        # Force parsedate_to_datetime to raise to hit exception branch
        monkeypatch.setattr(
            "amigo_sdk._retry_utils.parsedate_to_datetime",
            lambda _s: (_ for _ in ()).throw(ValueError("boom")),
        )
        assert parse_retry_after_seconds("Wed, 21 Oct 2015 07:28:00 GMT") is None

    # is_retryable_response
    def test_is_retryable_response_policy_get_and_post_429_with_header(self):
        methods = {"GET"}
        statuses = DEFAULT_RETRYABLE_STATUS
        assert is_retryable_response("GET", 500, {}, methods, statuses) is True
        assert (
            is_retryable_response("POST", 429, {"Retry-After": "1"}, methods, statuses)
            is True
        )
        assert is_retryable_response("POST", 429, {}, methods, statuses) is False

    def test_is_retryable_response_method_and_status_not_in_policies(self):
        methods = {"GET"}
        statuses = DEFAULT_RETRYABLE_STATUS
        assert is_retryable_response("POST", 500, {}, methods, statuses) is False
        assert is_retryable_response("GET", 418, {}, methods, statuses) is False

    def test_is_retryable_response_method_case_normalization(self):
        methods = {"GET"}
        statuses = DEFAULT_RETRYABLE_STATUS
        assert is_retryable_response("get", 500, {}, methods, statuses) is True

    # compute_retry_delay_seconds
    def test_compute_retry_delay_honors_retry_after_and_clamps(self):
        d = compute_retry_delay_seconds(1, 0.25, 0.5, "5.0")
        assert d == 0.5

    def test_compute_retry_delay_negative_retry_after_clamped_to_zero(self):
        d = compute_retry_delay_seconds(1, 0.25, 10.0, "-5.0")
        assert d == 0.0

    def test_compute_retry_delay_uses_backoff_when_no_retry_after(self, monkeypatch):
        # attempt=3 -> window = base * 2^(attempt-1) = 0.25 * 4 = 1.0; clamp to 0.75
        # We patch random.uniform to return upper bound to make deterministic
        called = {}

        def fake_uniform(a, b):
            called["args"] = (a, b)
            return b

        monkeypatch.setattr("amigo_sdk._retry_utils.random.uniform", fake_uniform)
        delay = compute_retry_delay_seconds(3, 0.25, 0.75, None)
        assert called["args"] == (0.0, 0.75)
        assert delay == 0.75

    def test_compute_retry_delay_with_retry_after_http_date(self):
        future_dt = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=1)
        http_date = format_datetime(future_dt)
        # Max is high, so we expect roughly ~1s (>=0)
        d = compute_retry_delay_seconds(1, 0.25, 30.0, http_date)
        assert d >= 0.0