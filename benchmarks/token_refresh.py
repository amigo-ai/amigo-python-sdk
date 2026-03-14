#!/usr/bin/env python3
"""Benchmark token refresh latency."""

import os
import time

import httpx

API_KEY = os.environ["AMIGO_API_KEY"]
API_KEY_ID = os.environ["AMIGO_API_KEY_ID"]
BASE_URL = os.environ.get("AMIGO_BASE_URL", "https://internal-api.amigo.ai")


def bench():
    times = []
    for _ in range(10):
        start = time.perf_counter()
        resp = httpx.post(
            f"{BASE_URL}/v1/sign-in",
            json={"api_key": API_KEY, "api_key_id": API_KEY_ID},
        )
        resp.raise_for_status()
        times.append((time.perf_counter() - start) * 1000)

    print("Token Refresh Latency:")
    print(f"  Cold start: {times[0]:.1f}ms")
    print(f"  Avg (warm): {sum(times[1:]) / len(times[1:]):.1f}ms")
    print(f"  Min: {min(times):.1f}ms")
    print(f"  Max: {max(times):.1f}ms")


if __name__ == "__main__":
    bench()
