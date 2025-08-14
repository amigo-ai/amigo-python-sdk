import asyncio
import json
import os
from collections.abc import AsyncGenerator
from pathlib import Path

from dotenv import load_dotenv

from amigo_sdk.errors import AmigoError, ConflictError, NotFoundError
from amigo_sdk.generated.model import (
    ConversationCreateConversationRequest,
    CreateConversationParametersQuery,
    GetConversationMessagesParametersQuery,
    InteractWithConversationParametersQuery,
)
from amigo_sdk.sdk_client import AmigoClient


async def run() -> None:
    # Load env vars from examples/.env (shared by all examples)
    examples_env = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=examples_env)

    service_id = os.getenv("AMIGO_SERVICE_ID")
    if not service_id:
        raise SystemExit(
            "Missing AMIGO_SERVICE_ID. Set it in your .env file (see .env.example)."
        )

    # AmigoClient reads other config from env (AMIGO_API_KEY, AMIGO_API_KEY_ID, AMIGO_USER_ID,
    # AMIGO_ORGANIZATION_ID, optional AMIGO_BASE_URL). You can also pass them explicitly.
    async with AmigoClient() as client:
        try:
            # 1) Create a conversation and log streamed events
            print("Creating conversation...")
            create_events = await client.conversation.create_conversation(
                ConversationCreateConversationRequest(
                    service_id=service_id, service_version_set_name="release"
                ),
                CreateConversationParametersQuery(response_format="text"),
            )

            result = await log_events("create", create_events)
            conversation_id = result.get("conversationId")
            if not conversation_id:
                raise RuntimeError("Conversation was not created (no id received).")

            # 2) Interact with the conversation via text and log streamed events
            print("Sending a text message to the conversation...")
            interaction_events = await client.conversation.interact_with_conversation(
                conversation_id,
                InteractWithConversationParametersQuery(
                    request_format="text", response_format="text"
                ),
                text_message="Hello from the Amigo Python SDK example!",
            )

            await log_events("interact", interaction_events)

            # 3) Get messages for the conversation and log them
            print("Fetching recent messages...")
            messages_page = await client.conversation.get_conversation_messages(
                conversation_id,
                GetConversationMessagesParametersQuery(
                    limit=10, sort_by=["+created_at"]
                ),
            )
            for m in getattr(messages_page, "messages", []) or []:
                print("[message]", json.dumps(m, indent=2))

            # 4) Finish the conversation
            print("Finishing conversation...")
            try:
                await client.conversation.finish_conversation(conversation_id)
                print("Conversation finished.")
            except (ConflictError, NotFoundError) as e:
                # Acceptable eventual-consistency outcomes
                print(f"Finish conversation warning: {type(e).__name__} - {e}")

            print("Done.")
        except AmigoError as err:
            # SDK error types include status code and optional context
            print(
                f"AmigoError ({type(err).__name__}) message={err} status_code={getattr(err, 'status_code', None)}"
            )
            raise SystemExit(1) from err
        except Exception as err:
            print("Unexpected error:", err)
            raise SystemExit(1) from err


async def log_events(label: str, events: AsyncGenerator) -> dict[str, str | None]:
    new_message_count = 0
    printed_ellipsis = False
    conversation_id: str | None = None

    async for evt in events:
        event = evt.model_dump()
        event_type = event.get("type", None)

        if event_type == "new-message":
            if new_message_count < 3:
                new_message_count += 1
                print(f"[{label} event] {json.dumps(event, indent=2)}")
            elif not printed_ellipsis:
                printed_ellipsis = True
                print(f"[{label} event] ... (more new-message events)")
        else:
            print(f"[{label} event] {json.dumps(event, indent=2)}")

        if event_type == "conversation-created":
            conversation_id = event.get("conversation_id", None)
        if event_type == "interaction-complete":
            break

    return {"conversationId": conversation_id}


if __name__ == "__main__":
    asyncio.run(run())
