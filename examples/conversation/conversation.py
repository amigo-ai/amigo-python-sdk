import asyncio
import json
import os
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

            conversation_id: str | None = None
            log_create = make_event_logger("create")
            async for evt in create_events:
                event = evt.model_dump(mode="json")
                log_create(event)
                if event.get("type") == "conversation-created":
                    conversation_id = event.get("conversation_id")

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

            log_interact = make_event_logger("interact")
            async for evt in interaction_events:
                event = evt.model_dump(mode="json")
                log_interact(event)
                if event.get("type") == "interaction-complete":
                    break

            # 3) Get messages for the conversation and log them
            print("Fetching recent messages...")
            messages_page = await client.conversation.get_conversation_messages(
                conversation_id,
                GetConversationMessagesParametersQuery(
                    limit=10, sort_by=["+created_at"]
                ),
            )
            for m in getattr(messages_page, "messages", []) or []:
                print("[message]", json.dumps(m.model_dump(mode="json"), indent=2))

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
            print(err)
            raise SystemExit(1) from err
        except Exception as err:
            print("Unexpected error:", err)
            raise SystemExit(1) from err


def make_event_logger(label: str):
    new_message_count = 0
    printed_ellipsis = False

    def _log(event: dict) -> None:
        nonlocal new_message_count, printed_ellipsis
        event_type = event.get("type")
        if event_type == "new-message":
            if new_message_count < 3:
                new_message_count += 1
                print(f"[{label} event] {json.dumps(event, indent=2)}")
            elif not printed_ellipsis:
                printed_ellipsis = True
                print(f"[{label} event] ... (more new-message events)")
            return
        print(f"[{label} event] {json.dumps(event, indent=2)}")

    return _log


if __name__ == "__main__":
    asyncio.run(run())
