import json
import os
from pathlib import Path

from dotenv import load_dotenv

from amigo_sdk import AmigoClient
from amigo_sdk.errors import AmigoError, ConflictError, NotFoundError
from amigo_sdk.models import (
    ConversationCreateConversationRequest,
    ConversationCreatedEvent,
    CreateConversationParametersQuery,
    CurrentAgentActionEvent,
    ErrorEvent,
    GetConversationMessagesParametersQuery,
    InteractionCompleteEvent,
    InteractWithConversationParametersQuery,
    NewMessageEvent,
    UserMessageAvailableEvent,
)


def handle_conversation_created(event: ConversationCreatedEvent) -> str:
    """Extract and return the conversation id."""
    return event.conversation_id


def handle_new_message(event: NewMessageEvent) -> str:
    """Return the message text (useful for accumulating partial text)."""
    return event.message


def handle_interaction_complete(event: InteractionCompleteEvent) -> tuple[str, str]:
    """Return the interaction id and full assistant message."""
    return event.interaction_id, event.full_message


def handle_user_message_available(event: UserMessageAvailableEvent) -> str:
    """Return the user message text for convenience."""
    return event.user_message


def handle_current_agent_action(_event: CurrentAgentActionEvent) -> None:
    """Placeholder for reacting to agent action updates (no-op in this example)."""
    return None


def handle_error(event: ErrorEvent) -> None:
    print("[error]", json.dumps(event.model_dump(mode="json"), indent=2))


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
                print(f"[{label} event] ... (more new-message events)\n")
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
            print("\nCreating conversation and handling streamed events (sync)...")

            create_events = client.conversation.create_conversation(
                ConversationCreateConversationRequest(service_id=service_id),
                CreateConversationParametersQuery(response_format="text"),
            )

            conversation_id: str | None = None
            log_create = make_event_logger("create")
            for evt in create_events:
                event_dict = evt.model_dump(mode="json")
                log_create(event_dict)
                e = evt.root
                if isinstance(e, ConversationCreatedEvent):
                    conversation_id = handle_conversation_created(e)
                elif isinstance(e, ErrorEvent):
                    handle_error(e)
                elif isinstance(e, InteractionCompleteEvent):
                    break

            print("\nCreated conversation:", conversation_id)

            print("\nInteracting with conversation (text, sync)...")

            interaction_events = client.conversation.interact_with_conversation(
                conversation_id,
                InteractWithConversationParametersQuery(
                    request_format="text", response_format="text"
                ),
                text_message=(
                    "Hello from the events example! Please tell me a fun fact about otters."
                ),
            )

            full_response = ""
            latest_interaction_id: str | None = None
            log_interact = make_event_logger("interact")
            for evt in interaction_events:
                event_dict = evt.model_dump(mode="json")
                log_interact(event_dict)
                e = evt.root
                if isinstance(e, InteractionCompleteEvent):
                    latest_interaction_id, full_response = handle_interaction_complete(
                        e
                    )
                    print("\nInteraction complete.\n")
                    break
                elif isinstance(e, ErrorEvent):
                    handle_error(e)

            if full_response:
                print("Full response:", full_response)
            if latest_interaction_id:
                print("Interaction id:", latest_interaction_id)

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
