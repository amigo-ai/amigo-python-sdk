"""
Example: Error handling patterns.

Demonstrates how to catch and inspect typed SDK errors,
including authentication failures, not-found errors, and rate limits.
"""

import os
import time

from dotenv import load_dotenv

from amigo_sdk import AmigoClient
from amigo_sdk.errors import (
    AmigoError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)
from amigo_sdk.models import GetConversationsParametersQuery


def main():
    # Load shared .env from the examples directory
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    # 1. Handling authentication errors
    print("1. Testing authentication error handling...")
    try:
        with AmigoClient(
            api_key="invalid-key",
            api_key_id="invalid-id",
            user_id="test-user",
            organization_id="test-org",
        ) as client:
            client.organization.get()
    except AuthenticationError as e:
        print(f"   Caught AuthenticationError: {e}")
        print(f"   Status code: {e.status_code}")

    # 2. Handling not-found errors
    print("\n2. Testing not-found error handling...")
    try:
        with AmigoClient() as client:
            client.conversation.finish_conversation("nonexistent-conversation-id")
    except NotFoundError as e:
        print(f"   Caught NotFoundError: {e}")
    except AuthenticationError:
        print("   (Authentication failed — set valid credentials in .env)")

    # 3. Inspecting error details
    print("\n3. Inspecting error properties...")
    try:
        with AmigoClient() as client:
            client.organization.get()
    except AmigoError as e:
        print(f"   Error type: {type(e).__name__}")
        print(f"   Message: {e}")
        print(f"   Status code: {getattr(e, 'status_code', 'N/A')}")
        print(f"   Error code: {getattr(e, 'error_code', 'N/A')}")

    # 4. Retry-on-rate-limit pattern
    print("\n4. Retry-on-rate-limit pattern (demo)...")

    def fetch_with_retry(client, max_retries=3):
        for attempt in range(max_retries):
            try:
                return client.conversation.get_conversations(
                    GetConversationsParametersQuery(limit=1)
                )
            except RateLimitError:
                if attempt < max_retries - 1:
                    wait = 2**attempt
                    print(f"   Rate limited, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

    try:
        with AmigoClient() as client:
            result = fetch_with_retry(client)
            print(f"   Success: {len(result.conversations)} conversations")
    except AmigoError as e:
        print(f"   {type(e).__name__}: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
