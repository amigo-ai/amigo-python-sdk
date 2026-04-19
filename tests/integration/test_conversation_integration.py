import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from amigo_sdk.errors import ConflictError, NotFoundError
from amigo_sdk.generated.model import (
    ConversationCreateConversationRequest,
    ConversationCreatedEvent,
    CreateConversationParametersQuery,
    ErrorEvent,
    GetConversationMessagesParametersQuery,
    GetConversationsParametersQuery,
    InteractionCompleteEvent,
    InteractWithConversationParametersQuery,
    NewMessageEvent,
    PCMUserMessageAudioConfig,
    SampleWidth,
)
from amigo_sdk.sdk_client import AmigoClient, AsyncAmigoClient

# Constants
SERVICE_ID = os.getenv("AMIGO_TEST_SERVICE_ID", "66e0da39f5a09fb3cf18ea75")


def _build_test_wav_bytes() -> bytes:
    """Load a short spoken WAV fixture for voice-request integration tests."""
    fixture_path = Path(__file__).with_name("fixtures") / "hello.wav"
    return fixture_path.read_bytes()


async def _latest_conversation_message_time_async(
    client: AsyncAmigoClient, conversation_id: str
) -> datetime:
    page = await client.conversations.get_conversation_messages(
        conversation_id,
        GetConversationMessagesParametersQuery(limit=1, sort_by=["-created_at"]),
    )
    if not page.messages:
        return datetime.now(UTC)
    latest = page.messages[0]
    return getattr(latest, "timestamp", None) or getattr(
        latest, "created_at", datetime.now(UTC)
    )


def _latest_conversation_message_time_sync(
    client: AmigoClient, conversation_id: str
) -> datetime:
    page = client.conversations.get_conversation_messages(
        conversation_id,
        GetConversationMessagesParametersQuery(limit=1, sort_by=["-created_at"]),
    )
    if not page.messages:
        return datetime.now(UTC)
    latest = page.messages[0]
    return getattr(latest, "timestamp", None) or getattr(
        latest, "created_at", datetime.now(UTC)
    )


async def _finish_open_conversations_async(client: AsyncAmigoClient) -> None:
    try:
        convs = await client.conversations.get_conversations(
            GetConversationsParametersQuery(
                service_id=[SERVICE_ID],
                is_finished=False,
                limit=25,
                sort_by=["-created_at"],
            )
        )
    except Exception:
        return

    for conversation in getattr(convs, "conversations", []) or []:
        try:
            await client.conversations.finish_conversation(conversation.id)
        except Exception:
            pass


def _finish_open_conversations_sync(client: AmigoClient) -> None:
    try:
        convs = client.conversations.get_conversations(
            GetConversationsParametersQuery(
                service_id=[SERVICE_ID],
                is_finished=False,
                limit=25,
                sort_by=["-created_at"],
            )
        )
    except Exception:
        return

    for conversation in getattr(convs, "conversations", []) or []:
        try:
            client.conversations.finish_conversation(conversation.id)
        except Exception:
            pass


def _require_bootstrap(
    test_class: type, *, require_interaction: bool = False
) -> tuple[str, str | None]:
    conversation_id = getattr(test_class, "conversation_id", None)
    if conversation_id is None:
        pytest.skip("Conversation bootstrap did not complete for this integration run.")

    interaction_id = getattr(test_class, "interaction_id", None)
    if require_interaction and interaction_id is None:
        pytest.skip("Interaction bootstrap did not complete for this integration run.")

    return conversation_id, interaction_id


async def _create_conversation_with_retry_async() -> tuple[str, str]:
    max_retries = 4

    for attempt in range(1, max_retries + 1):
        async with AsyncAmigoClient() as client:
            await _finish_open_conversations_async(client)

            try:
                events = await client.conversations.create_conversation(
                    body=ConversationCreateConversationRequest(
                        service_id=SERVICE_ID,
                        service_version_set_name="release",
                    ),
                    params=CreateConversationParametersQuery(response_format="text"),
                )
            except ConflictError:
                if attempt == max_retries:
                    pytest.skip(
                        "Classic conversation integration is currently busy; skipping transient 409 conflict."
                    )
                await asyncio.sleep(attempt + 1)
                continue

            conversation_id: str | None = None
            interaction_id: str | None = None
            saw_new_message = False

            async for resp in events:
                event = resp.root
                if isinstance(event, ErrorEvent):
                    pytest.fail(f"error event: {event.model_dump_json()}")
                if isinstance(event, ConversationCreatedEvent):
                    conversation_id = event.conversation_id
                elif isinstance(event, NewMessageEvent):
                    saw_new_message = True
                elif isinstance(event, InteractionCompleteEvent):
                    interaction_id = event.interaction_id
                    break

            assert conversation_id is not None
            assert interaction_id is not None
            assert saw_new_message is True
            return conversation_id, interaction_id

    pytest.fail("Failed to bootstrap async conversation integration tests.")


def _create_conversation_with_retry_sync() -> tuple[str, str]:
    import time

    max_retries = 4

    for attempt in range(1, max_retries + 1):
        with AmigoClient() as client:
            _finish_open_conversations_sync(client)

            try:
                events = client.conversations.create_conversation(
                    body=ConversationCreateConversationRequest(
                        service_id=SERVICE_ID,
                        service_version_set_name="release",
                    ),
                    params=CreateConversationParametersQuery(response_format="text"),
                )
            except ConflictError:
                if attempt == max_retries:
                    pytest.skip(
                        "Classic conversation integration is currently busy; skipping transient 409 conflict."
                    )
                time.sleep(attempt + 1)
                continue

            conversation_id: str | None = None
            interaction_id: str | None = None

            for resp in events:
                event = resp.root
                if isinstance(event, ErrorEvent):
                    pytest.fail(f"error event: {event.model_dump_json()}")
                if isinstance(event, ConversationCreatedEvent):
                    conversation_id = event.conversation_id
                elif isinstance(event, InteractionCompleteEvent):
                    interaction_id = event.interaction_id
                    break

            assert conversation_id is not None
            assert interaction_id is not None
            return conversation_id, interaction_id

    pytest.fail("Failed to bootstrap sync conversation integration tests.")


@pytest.fixture(scope="module", autouse=True)
async def pre_suite_cleanup() -> AsyncGenerator[None]:
    # Ensure env loaded and client can connect; verify service exists
    async with AsyncAmigoClient() as client:
        try:
            from amigo_sdk.generated.model import GetServicesParametersQuery

            services = await client.services.get_services(
                GetServicesParametersQuery(id=[SERVICE_ID])
            )
            service_ids = [
                getattr(s, "id", None) for s in getattr(services, "services", [])
            ]
            if service_ids and SERVICE_ID not in service_ids:
                pytest.skip(f"Service {SERVICE_ID} not found for this organization")
        except Exception:
            # If listing services fails, let tests surface the issue later
            pass

        # Finish any ongoing conversations for this service (best-effort)
        try:
            convs = await client.conversations.get_conversations(
                GetConversationsParametersQuery(
                    service_id=[SERVICE_ID],
                    is_finished=False,
                    limit=25,
                    sort_by=["-created_at"],
                )
            )
            for c in getattr(convs, "conversations", []) or []:
                try:
                    await client.conversations.finish_conversation(c.id)
                except Exception:
                    pass
        except Exception:
            pass

    # Allow eventual consistency to settle
    await asyncio.sleep(0.5)
    yield


@pytest.mark.integration
class TestConversationIntegration:
    conversation_id: str | None = None
    interaction_id: str | None = None

    async def test_create_conversation_streams_and_returns_ids(self):
        conversation_id, interaction_id = await _create_conversation_with_retry_async()
        type(self).conversation_id = conversation_id
        type(self).interaction_id = interaction_id

    async def test_recommend_responses_returns_suggestions(self):
        conversation_id, interaction_id = _require_bootstrap(
            type(self), require_interaction=True
        )

        async with AsyncAmigoClient() as client:
            recs = await client.conversations.recommend_responses_for_interaction(
                conversation_id, interaction_id
            )

            assert recs is not None
            assert isinstance(getattr(recs, "recommended_responses", None), list)

    async def test_get_conversations_filter_by_id(self):
        conversation_id, _ = _require_bootstrap(type(self))

        async with AsyncAmigoClient() as client:
            resp = await client.conversations.get_conversations(
                GetConversationsParametersQuery(id=[conversation_id])
            )

            assert resp is not None
            ids = [c.id for c in getattr(resp, "conversations", [])]
            assert conversation_id in ids

    async def test_interact_with_conversation_text_streams(self):
        conversation_id, _ = _require_bootstrap(type(self))

        async with AsyncAmigoClient() as client:
            events = await client.conversations.interact_with_conversation(
                conversation_id,
                params=InteractWithConversationParametersQuery(
                    request_format="text", response_format="text"
                ),
                text_message="Hello, I'm sending a text message from the Python SDK asynchronously!",
            )

            saw_interaction_complete = False
            latest_interaction_id: str | None = None
            event_count = 0

            async for evt in events:
                e = evt.root
                event_count += 1
                if isinstance(e, ErrorEvent):
                    pytest.fail(f"error event: {e.model_dump_json()}")
                if isinstance(e, InteractionCompleteEvent):
                    saw_interaction_complete = True
                    latest_interaction_id = e.interaction_id
                    break

            assert event_count > 0, "interact stream yielded no events"
            assert saw_interaction_complete is True, (
                f"no InteractionCompleteEvent in {event_count} events"
            )
            if latest_interaction_id:
                type(self).interaction_id = latest_interaction_id

    async def test_interact_with_conversation_external_event_streams(self):
        conversation_id, _ = _require_bootstrap(type(self))

        async with AsyncAmigoClient() as client:
            latest_message_time = await _latest_conversation_message_time_async(
                client, conversation_id
            )
            external_event_message_content = [
                "External event integration prelude #1.",
                "External event integration prelude #2.",
            ]
            external_event_message_timestamp = [
                latest_message_time + timedelta(seconds=1),
                latest_message_time + timedelta(seconds=2),
            ]
            assert len(external_event_message_timestamp) == len(
                external_event_message_content
            )
            events = await client.conversations.interact_with_conversation(
                conversation_id,
                params=InteractWithConversationParametersQuery(
                    request_format="text", response_format="text"
                ),
                initial_message_type="external-event",
                text_message="External event integration test message.",
                external_event_message_content=external_event_message_content,
                external_event_message_timestamp=external_event_message_timestamp,
            )

            saw_interaction_complete = False
            latest_interaction_id: str | None = None
            event_count = 0

            async for evt in events:
                e = evt.root
                event_count += 1
                if isinstance(e, ErrorEvent):
                    pytest.fail(f"error event: {e.model_dump_json()}")
                if isinstance(e, InteractionCompleteEvent):
                    saw_interaction_complete = True
                    latest_interaction_id = e.interaction_id
                    break

            assert event_count > 0, "external-event interact stream yielded no events"
            assert saw_interaction_complete is True, (
                f"no InteractionCompleteEvent in {event_count} events"
            )
            if latest_interaction_id:
                type(self).interaction_id = latest_interaction_id

    async def test_interact_with_conversation_voice_streams(self):
        conversation_id, _ = _require_bootstrap(type(self))

        async with AsyncAmigoClient() as client:
            events = await client.conversations.interact_with_conversation(
                conversation_id,
                params=InteractWithConversationParametersQuery(
                    request_format="voice",
                    response_format="text",
                    request_audio_config=PCMUserMessageAudioConfig(
                        type="pcm",
                        frame_rate=16000,
                        n_channels=1,
                        sample_width=SampleWidth.integer_2,
                    ),
                ),
                audio_bytes=_build_test_wav_bytes(),
                audio_content_type="audio/wav",
            )

            saw_interaction_complete = False
            latest_interaction_id: str | None = None
            event_count = 0

            async for evt in events:
                e = evt.root
                event_count += 1
                if isinstance(e, ErrorEvent):
                    pytest.fail(f"error event: {e.model_dump_json()}")
                if isinstance(e, InteractionCompleteEvent):
                    saw_interaction_complete = True
                    latest_interaction_id = e.interaction_id
                    break

            assert event_count > 0, "voice interact stream yielded no events"
            assert saw_interaction_complete is True, (
                f"no InteractionCompleteEvent in {event_count} events"
            )
            if latest_interaction_id:
                type(self).interaction_id = latest_interaction_id

    async def test_get_conversation_messages_pagination(self):
        conversation_id, _ = _require_bootstrap(type(self))

        async with AsyncAmigoClient() as client:
            page1 = await client.conversations.get_conversation_messages(
                conversation_id,
                GetConversationMessagesParametersQuery(
                    limit=1, sort_by=["+created_at"]
                ),
            )
            assert page1 is not None
            assert isinstance(getattr(page1, "messages", None), list)
            assert len(page1.messages) == 1
            assert isinstance(page1.has_more, bool)

            if page1.has_more:
                assert page1.continuation_token is not None
                page2 = await client.conversations.get_conversation_messages(
                    conversation_id,
                    GetConversationMessagesParametersQuery(
                        limit=1,
                        continuation_token=page1.continuation_token,
                        sort_by=["+created_at"],
                    ),
                )
                assert page2 is not None
                assert isinstance(getattr(page2, "messages", None), list)
                assert len(page2.messages) == 1

    async def test_get_interaction_insights_returns_data(self):
        conversation_id, interaction_id = _require_bootstrap(
            type(self), require_interaction=True
        )

        async with AsyncAmigoClient() as client:
            insights = await client.conversations.get_interaction_insights(
                conversation_id, interaction_id
            )
            assert insights is not None
            assert isinstance(getattr(insights, "current_state_name", None), str)

    async def test_finish_conversation_returns_acceptable_outcome(self):
        conversation_id, _ = _require_bootstrap(type(self))

        async with AsyncAmigoClient() as client:
            try:
                await client.conversations.finish_conversation(conversation_id)
            except Exception as e:
                # Accept eventual-consistency errors
                assert isinstance(e, (ConflictError, NotFoundError))


@pytest.mark.integration
class TestConversationIntegrationSync:
    conversation_id: str | None = None
    interaction_id: str | None = None

    def test_create_conversation_streams_and_returns_ids(self):
        conversation_id, interaction_id = _create_conversation_with_retry_sync()
        type(self).conversation_id = conversation_id
        type(self).interaction_id = interaction_id

    def test_recommend_responses_returns_suggestions(self):
        conversation_id, interaction_id = _require_bootstrap(
            type(self), require_interaction=True
        )

        with AmigoClient() as client:
            recs = client.conversations.recommend_responses_for_interaction(
                conversation_id, interaction_id
            )

            assert recs is not None
            assert isinstance(getattr(recs, "recommended_responses", None), list)

    def test_get_conversations_filter_by_id(self):
        conversation_id, _ = _require_bootstrap(type(self))

        with AmigoClient() as client:
            resp = client.conversations.get_conversations(
                GetConversationsParametersQuery(id=[conversation_id])
            )

            assert resp is not None
            ids = [c.id for c in getattr(resp, "conversations", [])]
            assert conversation_id in ids

    def test_interact_with_conversation_text_streams(self):
        conversation_id, _ = _require_bootstrap(type(self))

        with AmigoClient() as client:
            events = client.conversations.interact_with_conversation(
                conversation_id,
                params=InteractWithConversationParametersQuery(
                    request_format="text", response_format="text"
                ),
                initial_message_type="user-message",
                text_message="Hello, I'm sending a text message from the Python SDK synchronously!",
            )

            saw_interaction_complete = False
            latest_interaction_id: str | None = None
            event_count = 0

            for evt in events:
                e = evt.root
                event_count += 1
                if isinstance(e, ErrorEvent):
                    pytest.fail(f"error event: {e.model_dump_json()}")
                if isinstance(e, InteractionCompleteEvent):
                    saw_interaction_complete = True
                    latest_interaction_id = e.interaction_id
                    break

            assert event_count > 0, "sync interact stream yielded no events"
            assert saw_interaction_complete is True, (
                f"no InteractionCompleteEvent in {event_count} events (sync)"
            )
            if latest_interaction_id:
                type(self).interaction_id = latest_interaction_id

    def test_interact_with_conversation_external_event_streams(self):
        conversation_id, _ = _require_bootstrap(type(self))

        with AmigoClient() as client:
            latest_message_time = _latest_conversation_message_time_sync(
                client, conversation_id
            )
            external_event_message_content = [
                "External event integration prelude #1.",
                "External event integration prelude #2.",
            ]
            external_event_message_timestamp = [
                latest_message_time + timedelta(seconds=1),
                latest_message_time + timedelta(seconds=2),
            ]
            assert len(external_event_message_timestamp) == len(
                external_event_message_content
            )
            events = client.conversations.interact_with_conversation(
                conversation_id,
                params=InteractWithConversationParametersQuery(
                    request_format="text", response_format="text"
                ),
                initial_message_type="external-event",
                text_message="External event integration test message.",
                external_event_message_content=external_event_message_content,
                external_event_message_timestamp=external_event_message_timestamp,
            )

            saw_interaction_complete = False
            latest_interaction_id: str | None = None
            event_count = 0

            for evt in events:
                e = evt.root
                event_count += 1
                if isinstance(e, ErrorEvent):
                    pytest.fail(f"error event: {e.model_dump_json()}")
                if isinstance(e, InteractionCompleteEvent):
                    saw_interaction_complete = True
                    latest_interaction_id = e.interaction_id
                    break

            assert event_count > 0, "sync external-event stream yielded no events"
            assert saw_interaction_complete is True, (
                f"no InteractionCompleteEvent in {event_count} events"
            )
            if latest_interaction_id:
                type(self).interaction_id = latest_interaction_id

    def test_interact_with_conversation_voice_streams(self):
        conversation_id, _ = _require_bootstrap(type(self))

        with AmigoClient() as client:
            events = client.conversations.interact_with_conversation(
                conversation_id,
                params=InteractWithConversationParametersQuery(
                    request_format="voice",
                    response_format="text",
                    request_audio_config=PCMUserMessageAudioConfig(
                        type="pcm",
                        frame_rate=16000,
                        n_channels=1,
                        sample_width=SampleWidth.integer_2,
                    ),
                ),
                audio_bytes=_build_test_wav_bytes(),
                audio_content_type="audio/wav",
            )

            saw_interaction_complete = False
            latest_interaction_id: str | None = None
            event_count = 0

            for evt in events:
                e = evt.root
                event_count += 1
                if isinstance(e, ErrorEvent):
                    pytest.fail(f"error event: {e.model_dump_json()}")
                if isinstance(e, InteractionCompleteEvent):
                    saw_interaction_complete = True
                    latest_interaction_id = e.interaction_id
                    break

            assert event_count > 0, "sync voice stream yielded no events"
            assert saw_interaction_complete is True, (
                f"no InteractionCompleteEvent in {event_count} events"
            )
            if latest_interaction_id:
                type(self).interaction_id = latest_interaction_id

    def test_get_conversation_messages_pagination(self):
        conversation_id, _ = _require_bootstrap(type(self))

        with AmigoClient() as client:
            page1 = client.conversations.get_conversation_messages(
                conversation_id,
                GetConversationMessagesParametersQuery(
                    limit=1, sort_by=["+created_at"]
                ),
            )
            assert page1 is not None
            assert isinstance(getattr(page1, "messages", None), list)
            assert len(page1.messages) == 1
            assert isinstance(page1.has_more, bool)

            if page1.has_more:
                assert page1.continuation_token is not None
                page2 = client.conversations.get_conversation_messages(
                    conversation_id,
                    GetConversationMessagesParametersQuery(
                        limit=1,
                        continuation_token=page1.continuation_token,
                        sort_by=["+created_at"],
                    ),
                )
                assert page2 is not None
                assert isinstance(getattr(page2, "messages", None), list)
                assert len(page2.messages) == 1

    def test_get_interaction_insights_returns_data(self):
        conversation_id, interaction_id = _require_bootstrap(
            type(self), require_interaction=True
        )

        with AmigoClient() as client:
            insights = client.conversations.get_interaction_insights(
                conversation_id, interaction_id
            )
            assert insights is not None
            assert isinstance(getattr(insights, "current_state_name", None), str)

    def test_finish_conversation_returns_acceptable_outcome(self):
        conversation_id, _ = _require_bootstrap(type(self))

        with AmigoClient() as client:
            try:
                client.conversations.finish_conversation(conversation_id)
            except Exception as e:
                assert isinstance(e, (ConflictError, NotFoundError))
