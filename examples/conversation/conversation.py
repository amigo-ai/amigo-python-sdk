import json
import os
from pathlib import Path

from dotenv import load_dotenv

from amigo_sdk.errors import AmigoError, ConflictError, NotFoundError
from amigo_sdk.generated.model import (
    ConversationCreateConversationRequest,
    CreateConversationParametersQuery,
    GetConversationMessagesParametersQuery,
    GetConversationsParametersQuery,
    InteractWithConversationParametersQuery,
)
from amigo_sdk.sdk_client import AmigoClient


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


def run() -> None:
    # Load env vars from examples/.env (shared by all examples)
    examples_env = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=examples_env)

    service_id = os.getenv("AMIGO_SERVICE_ID")
    if not service_id:
        raise SystemExit(
            "Missing AMIGO_SERVICE_ID. Set it in your .env file (see .env.example)."
        )

    with AmigoClient() as client:
        try:
            print("Creating conversation (sync)...")
            create_events = client.conversation.create_conversation(
                ConversationCreateConversationRequest(service_id=service_id),
                CreateConversationParametersQuery(response_format="text"),
            )

            conversation_id: str | None = None
            log_create = make_event_logger("create")
            for evt in create_events:
                event = evt.model_dump(mode="json")
                log_create(event)
                if event.get("type") == "conversation-created":
                    conversation_id = event.get("conversation_id")
                if event.get("type") == "interaction-complete":
                    break

            if not conversation_id:
                raise RuntimeError("Conversation was not created (no id received).")

            print("\nGetting conversation (sync)...")
            conversation = client.conversation.get_conversations(
                GetConversationsParametersQuery(id=[conversation_id])
            )
            print(
                json.dumps(
                    conversation.conversations[0].model_dump(mode="json"), indent=2
                ),
            )

            print("\nSending a text message to the conversation (sync)...")
            interaction_events = client.conversation.interact_with_conversation(
                conversation_id,
                InteractWithConversationParametersQuery(
                    request_format="text", response_format="text"
                ),
                text_message="Hello from the Amigo Python SDK sync example!",
            )
            log_interact = make_event_logger("interact")
            for evt in interaction_events:
                event = evt.model_dump(mode="json")
                log_interact(event)
                if event.get("type") == "interaction-complete":
                    break

            print("\nFetching recent messages (sync)...")
            messages_page = client.conversation.get_conversation_messages(
                conversation_id,
                GetConversationMessagesParametersQuery(
                    limit=10, sort_by=["+created_at"]
                ),
            )
            for m in getattr(messages_page, "messages", []) or []:
                print("[message]", json.dumps(m.model_dump(mode="json"), indent=2))

            print("\nFinishing conversation (sync)...")
            try:
                client.conversation.finish_conversation(conversation_id)
                print("Conversation finished.")
            except (ConflictError, NotFoundError) as e:
                print(f"Finish conversation warning: {type(e).__name__} - {e}")

            print("Done.")
        except AmigoError as err:
            print(err)
            raise SystemExit(1) from err
        except Exception as err:
            print("Unexpected error:", err)
            raise SystemExit(1) from err


if __name__ == "__main__":
    run()
