"""
Example: Using the async client.

Demonstrates the AsyncAmigoClient with async/await patterns,
including concurrent operations with asyncio.gather.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

from amigo_sdk import AsyncAmigoClient
from amigo_sdk.models import (
    ConversationCreateConversationRequest,
    CreateConversationParametersQuery,
    GetConversationsParametersQuery,
    InteractWithConversationParametersQuery,
)


async def main():
    # Load shared .env from the examples directory
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    service_id = os.environ.get("AMIGO_SERVICE_ID")
    if not service_id:
        print("Set AMIGO_SERVICE_ID in your .env file")
        sys.exit(1)

    async with AsyncAmigoClient() as client:
        # Fetch organization info and recent conversations concurrently
        print("Fetching org info and conversations concurrently...")
        org, conversations = await asyncio.gather(
            client.organization.get(),
            client.conversation.get_conversations(
                GetConversationsParametersQuery(limit=5, sort_by=["-created_at"])
            ),
        )
        print(f"Organization: {org.name}")
        print(f"Recent conversations: {len(conversations.conversations)}")

        # Create a conversation
        print("\nCreating conversation...")
        create_stream = await client.conversation.create_conversation(
            body=ConversationCreateConversationRequest(service_id=service_id),
            params=CreateConversationParametersQuery(),
        )

        conversation_id = None
        async for event in create_stream:
            if hasattr(event.root, "conversation_id"):
                conversation_id = event.root.conversation_id

        if not conversation_id:
            print("Failed to get conversation_id")
            sys.exit(1)

        print(f"Conversation created: {conversation_id}")

        # Interact with the conversation
        print("\nSending message...")
        interaction_stream = await client.conversation.interact_with_conversation(
            conversation_id=conversation_id,
            params=InteractWithConversationParametersQuery(request_format="text"),
            text_message="What services do you provide?",
        )

        async for event in interaction_stream:
            if hasattr(event.root, "text"):
                print(event.root.text, end="", flush=True)

        print()

        # Finish
        await client.conversation.finish_conversation(conversation_id)
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
