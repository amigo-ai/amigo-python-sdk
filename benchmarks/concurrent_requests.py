#!/usr/bin/env python3
"""Benchmark concurrent request handling."""
import asyncio
import os
import time

import httpx

API_KEY = os.environ["AMIGO_API_KEY"]
API_KEY_ID = os.environ["AMIGO_API_KEY_ID"]
BASE_URL = os.environ.get("AMIGO_BASE_URL", "https://internal-api.amigo.ai")
USER_ID = os.environ["AMIGO_USER_ID"]
ORG_ID = os.environ.get("AMIGO_ORG_ID", "dogfood")


async def get_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/v1/sign-in",
            json={"api_key": API_KEY, "api_key_id": API_KEY_ID},
        )
        return resp.json()["access_token"]


async def bench_concurrent(n: int, token: str):
    async with httpx.AsyncClient() as client:
        start = time.perf_counter()
        tasks = [
            client.get(
                f"{BASE_URL}/v1/{ORG_ID}/service/",
                headers={"Authorization": f"Bearer {token}", "x-user-id": USER_ID},
            )
            for _ in range(n)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = (time.perf_counter() - start) * 1000
        ok = sum(1 for r in results if not isinstance(r, Exception))
        failed = n - ok
        rps = n / (elapsed / 1000)
        print(f"  {n} parallel: {elapsed:.0f}ms ({ok} ok, {failed} failed, {rps:.1f} req/s)")


async def main():
    print("Concurrent Request Handling:")
    token = await get_token()
    for n in [10, 50, 100]:
        await bench_concurrent(n, token)


if __name__ == "__main__":
    asyncio.run(main())
