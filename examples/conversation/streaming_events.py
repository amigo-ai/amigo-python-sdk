"""
Example: Streaming conversation events with typed event handling.

Demonstrates how to create a conversation and process NDJSON stream events,
dispatching on event type to handle partial text, completion, and other events.
"""

import os
import sys

from dotenv import load_dotenv

from amigo_sdk import AmigoClient
from amigo_sdk.models import (
    ConversationCreateConversationRequest,
    CreateConversationParametersQuery,
    InteractWithConversationParametersQuery,
)


def main():
    # Load shared .env from the examples directory
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    service_id = os.environ.get("AMIGO_SERVICE_ID")
    if not service_id:
        print("Set AMIGO_SERVICE_ID in your .env file")
        sys.exit(1)

    with AmigoClient() as client:
        # 1. Create a conversation (streamed)
        print("Creating conversation...")
        create_events = client.conversation.create_conversation(
            body=ConversationCreateConversationRequest(service_id=service_id),
            params=CreateConversationParametersQuery(),
        )

        conversation_id = None
        for event in create_events:
            root = event.root
            event_type = type(root).__name__
            print(f"  [{event_type}]")

            # Extract conversation_id from the first event that has it
            if hasattr(root, "conversation_id"):
                conversation_id = root.conversation_id

        if not conversation_id:
            print("Failed to get conversation_id from stream")
            sys.exit(1)

        print(f"\nConversation created: {conversation_id}")

        # 2. Interact and stream response events
        print("\nSending message and streaming events...")
        interaction_events = client.conversation.interact_with_conversation(
            conversation_id=conversation_id,
            params=InteractWithConversationParametersQuery(request_format="text"),
            text_message="Hello, how can you help me today?",
        )

        for event in interaction_events:
            root = event.root
            event_type = type(root).__name__

            # Handle different event types
            if hasattr(root, "text"):
                # Partial text events — print without newline for streaming effect
                print(root.text, end="", flush=True)
            elif event_type == "InteractionCompleteEvent":
                print("\n  [Interaction complete]")
            else:
                print(f"  [{event_type}]")

        # 3. Clean up
        print("\nFinishing conversation...")
        client.conversation.finish_conversation(conversation_id)
        print("Done.")


if __name__ == "__main__":
    main()
