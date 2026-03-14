import asyncio
import json
import threading
from collections.abc import AsyncGenerator, Iterator
from datetime import datetime
from typing import Literal, TypedDict

from pydantic import AnyUrl, BaseModel

from amigo_sdk.generated.model import (
    ConversationCreateConversationRequest,
    ConversationCreateConversationResponse,
    ConversationEvent,
    ConversationGenerateConversationStarterRequest,
    ConversationGenerateConversationStarterResponse,
    ConversationGetConversationMessagesResponse,
    ConversationGetConversationsResponse,
    ConversationGetInteractionInsightsResponse,
    ConversationInteractWithConversationResponse,
    ConversationRecommendResponsesForInteractionResponse,
    CreateConversationParametersQuery,
    Format,
    GetConversationMessagesParametersQuery,
    GetConversationsParametersQuery,
    InteractWithConversationParametersQuery,
)
from amigo_sdk.http_client import AmigoAsyncHttpClient, AmigoHttpClient


class InteractionInput(TypedDict, total=False):
    """Typed dictionary for interact_with_conversation keyword arguments."""

    initial_message_type: Literal["user-message", "external-event"]
    text_message: str | None
    audio_bytes: bytes | None
    audio_content_type: Literal["audio/mpeg", "audio/wav"] | None
    external_event_message_content: list[str] | None
    external_event_message_timestamp: list[datetime] | None


class _StreamRequestKwargs(TypedDict, total=False):
    """Typed kwargs for HTTP streaming requests (replaces dict[str, Any])."""

    params: dict[str, str | int | float | bool]
    headers: dict[str, str]
    abort_event: asyncio.Event | threading.Event | None
    files: list[tuple[str, tuple[str | None, str | bytes, str]]]


class GetMessageSourceResponse(BaseModel):
    """Response model for the get_message_source endpoint."""

    url: AnyUrl
    expires_at: datetime
    content_type: Literal["audio/mpeg", "audio/wav"]


def _build_interact_form_data(
    *,
    initial_message_type: Literal["user-message", "external-event"],
    external_event_message_content: list[str] | None,
    external_event_message_timestamp: list[datetime] | None,
) -> list[tuple[str, tuple[None, str]]]:
    """Build multipart form-data fields for the interact endpoint."""
    data: list[tuple[str, tuple[None, str]]] = [
        ("initial_message_type", (None, initial_message_type))
    ]
    for content in external_event_message_content or []:
        data.append(("external_event_message_content", (None, content)))
    for timestamp in external_event_message_timestamp or []:
        data.append(("external_event_message_timestamp", (None, timestamp.isoformat())))
    return data


class AsyncConversationResource:
    """Conversation resource for Amigo API operations."""

    def __init__(self, http_client: AmigoAsyncHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    async def create_conversation(
        self,
        body: ConversationCreateConversationRequest,
        params: CreateConversationParametersQuery,
        abort_event: asyncio.Event | None = None,
    ) -> "AsyncGenerator[ConversationCreateConversationResponse]":
        """Create a new conversation and stream NDJSON events.

        Returns an async generator yielding `ConversationCreateConversationResponse` events.
        """

        async def _generator():
            async for line in self._http.stream_lines(
                "POST",
                f"/v1/{self._organization_id}/conversation/",
                params=params.model_dump(mode="json", exclude_none=True),
                json=body.model_dump(mode="json", exclude_none=True),
                headers={"Accept": "application/x-ndjson"},
                abort_event=abort_event,
            ):
                # Each line is a JSON object representing a discriminated union event
                yield ConversationCreateConversationResponse.model_validate_json(line)

        return _generator()

    async def interact_with_conversation(
        self,
        conversation_id: str,
        params: InteractWithConversationParametersQuery,
        abort_event: asyncio.Event | None = None,
        *,
        initial_message_type: Literal[
            "user-message", "external-event"
        ] = "user-message",
        text_message: str | None = None,
        audio_bytes: bytes | None = None,
        audio_content_type: Literal["audio/mpeg", "audio/wav"] | None = None,
        external_event_message_content: list[str] | None = None,
        external_event_message_timestamp: list[datetime] | None = None,
    ) -> "AsyncGenerator[ConversationInteractWithConversationResponse]":
        """Interact with a conversation and stream NDJSON events.

        Returns an async generator yielding `ConversationInteractWithConversationResponse` events.
        """

        async def _generator():
            params_data = params.model_dump(mode="json", exclude_none=True)
            if "request_audio_config" in params_data:
                params_data["request_audio_config"] = json.dumps(
                    params_data["request_audio_config"]
                )
            request_kwargs: _StreamRequestKwargs = {
                "params": params_data,
                "abort_event": abort_event,
                "headers": {"Accept": "application/x-ndjson"},
            }

            if initial_message_type not in {"user-message", "external-event"}:
                raise ValueError(
                    "initial_message_type must be 'user-message' or 'external-event'"
                )

            if params.request_format == Format.text:
                if text_message is None:
                    raise ValueError(
                        "text_message is required when request_format is 'text'"
                    )
                text_bytes = text_message.encode("utf-8")
                form_fields = _build_interact_form_data(
                    initial_message_type=initial_message_type,
                    external_event_message_content=external_event_message_content,
                    external_event_message_timestamp=external_event_message_timestamp,
                )
                request_kwargs["files"] = form_fields + [
                    (
                        "recorded_message",
                        ("message.txt", text_bytes, "text/plain; charset=utf-8"),
                    )
                ]
            elif params.request_format == Format.voice:
                if audio_bytes is None or audio_content_type is None:
                    raise ValueError(
                        "audio_bytes and audio_content_type are required when request_format is 'voice'"
                    )
                ext = "mp3" if audio_content_type == "audio/mpeg" else "wav"
                form_fields = _build_interact_form_data(
                    initial_message_type=initial_message_type,
                    external_event_message_content=external_event_message_content,
                    external_event_message_timestamp=external_event_message_timestamp,
                )
                request_kwargs["files"] = form_fields + [
                    (
                        "recorded_message",
                        (f"audio.{ext}", audio_bytes, audio_content_type),
                    )
                ]
            else:
                raise ValueError("Unsupported or missing request_format in params")

            async for line in self._http.stream_lines(
                "POST",
                f"/v1/{self._organization_id}/conversation/{conversation_id}/interact",
                **request_kwargs,
            ):
                # Each line is a JSON object representing a discriminated union event.
                # The response wraps events in ConversationEvent RootModel; unwrap
                # so callers get concrete event types directly.
                parsed = (
                    ConversationInteractWithConversationResponse.model_validate_json(
                        line
                    )
                )
                event = parsed.root
                if isinstance(event, ConversationEvent):
                    parsed.root = event.root
                yield parsed

        return _generator()

    async def finish_conversation(self, conversation_id: str) -> None:
        """Finish a conversation."""
        await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/finish/",
        )

    async def get_conversations(
        self, params: GetConversationsParametersQuery
    ) -> ConversationGetConversationsResponse:
        """Get conversations."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/conversation/",
            params=params.model_dump(mode="json", exclude_none=True),
        )
        return ConversationGetConversationsResponse.model_validate_json(response.text)

    async def get_conversation_messages(
        self, conversation_id: str, params: GetConversationMessagesParametersQuery
    ) -> ConversationGetConversationMessagesResponse:
        """Get conversation messages."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/messages/",
            params=params.model_dump(
                mode="json", exclude_none=True, exclude_defaults=True
            ),
        )
        return ConversationGetConversationMessagesResponse.model_validate_json(
            response.text
        )

    async def recommend_responses_for_interaction(
        self, conversation_id: str, interaction_id: str
    ) -> ConversationRecommendResponsesForInteractionResponse:
        """Recommend responses for an interaction."""
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/interaction/{interaction_id}/recommend_responses",
        )
        return ConversationRecommendResponsesForInteractionResponse.model_validate_json(
            response.text
        )

    async def get_interaction_insights(
        self, conversation_id: str, interaction_id: str
    ) -> ConversationGetInteractionInsightsResponse:
        """Get insights for an interaction."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/interaction/{interaction_id}/insights",
        )
        return ConversationGetInteractionInsightsResponse.model_validate_json(
            response.text
        )

    async def get_message_source(
        self, conversation_id: str, message_id: str
    ) -> GetMessageSourceResponse:
        """Get the source of a message."""
        response = await self._http.request(
            "GET",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/messages/{message_id}/source",
        )
        return GetMessageSourceResponse.model_validate_json(response.text)

    async def generate_conversation_starters(
        self, body: ConversationGenerateConversationStarterRequest
    ) -> ConversationGenerateConversationStarterResponse:
        """Generate conversation starters."""
        response = await self._http.request(
            "POST",
            f"/v1/{self._organization_id}/conversation/conversation_starter",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return ConversationGenerateConversationStarterResponse.model_validate_json(
            response.text
        )

    # --- Convenience aliases ---

    async def list(
        self, params: GetConversationsParametersQuery
    ) -> ConversationGetConversationsResponse:
        """Alias for get_conversations."""
        return await self.get_conversations(params)

    def create(self, *args, **kwargs):
        """Alias for create_conversation."""
        return self.create_conversation(*args, **kwargs)

    def interact(self, *args, **kwargs):
        """Alias for interact_with_conversation."""
        return self.interact_with_conversation(*args, **kwargs)

    async def finish(self, conversation_id: str) -> None:
        """Alias for finish_conversation."""
        return await self.finish_conversation(conversation_id)

    async def messages(
        self, conversation_id: str, params: GetConversationMessagesParametersQuery
    ) -> ConversationGetConversationMessagesResponse:
        """Alias for get_conversation_messages."""
        return await self.get_conversation_messages(conversation_id, params)


class ConversationResource:
    """Conversation resource for synchronous operations."""

    def __init__(self, http_client: AmigoHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    def create_conversation(
        self,
        body: ConversationCreateConversationRequest,
        params: CreateConversationParametersQuery,
        abort_event: threading.Event | None = None,
    ) -> Iterator[ConversationCreateConversationResponse]:
        """Create a new conversation and stream NDJSON events."""

        def _iter():
            for line in self._http.stream_lines(
                "POST",
                f"/v1/{self._organization_id}/conversation/",
                params=params.model_dump(mode="json", exclude_none=True),
                json=body.model_dump(mode="json", exclude_none=True),
                headers={"Accept": "application/x-ndjson"},
                abort_event=abort_event,
            ):
                yield ConversationCreateConversationResponse.model_validate_json(line)

        return _iter()

    def interact_with_conversation(
        self,
        conversation_id: str,
        params: InteractWithConversationParametersQuery,
        abort_event: threading.Event | None = None,
        *,
        initial_message_type: Literal[
            "user-message", "external-event"
        ] = "user-message",
        text_message: str | None = None,
        audio_bytes: bytes | None = None,
        audio_content_type: Literal["audio/mpeg", "audio/wav"] | None = None,
        external_event_message_content: list[str] | None = None,
        external_event_message_timestamp: list[datetime] | None = None,
    ) -> Iterator[ConversationInteractWithConversationResponse]:
        """Interact with a conversation and stream NDJSON events."""

        def _iter():
            params_data = params.model_dump(mode="json", exclude_none=True)
            if "request_audio_config" in params_data:
                params_data["request_audio_config"] = json.dumps(
                    params_data["request_audio_config"]
                )
            request_kwargs: _StreamRequestKwargs = {
                "params": params_data,
                "headers": {"Accept": "application/x-ndjson"},
                "abort_event": abort_event,
            }

            if initial_message_type not in {"user-message", "external-event"}:
                raise ValueError(
                    "initial_message_type must be 'user-message' or 'external-event'"
                )

            req_format = getattr(params, "request_format", None)
            if req_format == Format.text:
                if text_message is None:
                    raise ValueError(
                        "text_message is required when request_format is 'text'"
                    )
                text_bytes = text_message.encode("utf-8")
                form_fields = _build_interact_form_data(
                    initial_message_type=initial_message_type,
                    external_event_message_content=external_event_message_content,
                    external_event_message_timestamp=external_event_message_timestamp,
                )
                request_kwargs["files"] = form_fields + [
                    (
                        "recorded_message",
                        ("message.txt", text_bytes, "text/plain; charset=utf-8"),
                    )
                ]
            elif req_format == Format.voice:
                if audio_bytes is None or audio_content_type is None:
                    raise ValueError(
                        "audio_bytes and audio_content_type are required when request_format is 'voice'"
                    )
                ext = "mp3" if audio_content_type == "audio/mpeg" else "wav"
                form_fields = _build_interact_form_data(
                    initial_message_type=initial_message_type,
                    external_event_message_content=external_event_message_content,
                    external_event_message_timestamp=external_event_message_timestamp,
                )
                request_kwargs["files"] = form_fields + [
                    (
                        "recorded_message",
                        (f"audio.{ext}", audio_bytes, audio_content_type),
                    )
                ]
            else:
                raise ValueError("Unsupported or missing request_format in params")

            for line in self._http.stream_lines(
                "POST",
                f"/v1/{self._organization_id}/conversation/{conversation_id}/interact",
                **request_kwargs,
            ):
                parsed = (
                    ConversationInteractWithConversationResponse.model_validate_json(
                        line
                    )
                )
                event = parsed.root
                if isinstance(event, ConversationEvent):
                    parsed.root = event.root
                yield parsed

        return _iter()

    def finish_conversation(self, conversation_id: str) -> None:
        """Finish a conversation."""
        self._http.request(
            "POST",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/finish/",
        )

    def get_conversations(
        self, params: GetConversationsParametersQuery
    ) -> ConversationGetConversationsResponse:
        """Get a list of conversations matching the query parameters."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/conversation/",
            params=params.model_dump(mode="json", exclude_none=True),
        )
        return ConversationGetConversationsResponse.model_validate_json(response.text)

    def get_conversation_messages(
        self, conversation_id: str, params: GetConversationMessagesParametersQuery
    ) -> ConversationGetConversationMessagesResponse:
        """Get messages for a conversation."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/messages/",
            params=params.model_dump(
                mode="json", exclude_none=True, exclude_defaults=True
            ),
        )
        return ConversationGetConversationMessagesResponse.model_validate_json(
            response.text
        )

    def recommend_responses_for_interaction(
        self, conversation_id: str, interaction_id: str
    ) -> ConversationRecommendResponsesForInteractionResponse:
        """Get recommended responses for an interaction."""
        response = self._http.request(
            "POST",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/interaction/{interaction_id}/recommend_responses",
        )
        return ConversationRecommendResponsesForInteractionResponse.model_validate_json(
            response.text
        )

    def get_interaction_insights(
        self, conversation_id: str, interaction_id: str
    ) -> ConversationGetInteractionInsightsResponse:
        """Get insights for an interaction."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/interaction/{interaction_id}/insights",
        )
        return ConversationGetInteractionInsightsResponse.model_validate_json(
            response.text
        )

    def get_message_source(
        self, conversation_id: str, message_id: str
    ) -> GetMessageSourceResponse:
        """Get the audio/media source URL for a message."""
        response = self._http.request(
            "GET",
            f"/v1/{self._organization_id}/conversation/{conversation_id}/messages/{message_id}/source",
        )
        return GetMessageSourceResponse.model_validate_json(response.text)

    def generate_conversation_starters(
        self, body: ConversationGenerateConversationStarterRequest
    ) -> ConversationGenerateConversationStarterResponse:
        """Generate conversation starter suggestions."""
        response = self._http.request(
            "POST",
            f"/v1/{self._organization_id}/conversation/conversation_starter",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return ConversationGenerateConversationStarterResponse.model_validate_json(
            response.text
        )

    # --- Convenience aliases ---

    def list(
        self, params: GetConversationsParametersQuery
    ) -> ConversationGetConversationsResponse:
        """Alias for get_conversations."""
        return self.get_conversations(params)

    def create(self, *args, **kwargs):
        """Alias for create_conversation."""
        return self.create_conversation(*args, **kwargs)

    def interact(self, *args, **kwargs):
        """Alias for interact_with_conversation."""
        return self.interact_with_conversation(*args, **kwargs)

    def finish(self, conversation_id: str) -> None:
        """Alias for finish_conversation."""
        return self.finish_conversation(conversation_id)

    def messages(
        self, conversation_id: str, params: GetConversationMessagesParametersQuery
    ) -> ConversationGetConversationMessagesResponse:
        """Alias for get_conversation_messages."""
        return self.get_conversation_messages(conversation_id, params)
