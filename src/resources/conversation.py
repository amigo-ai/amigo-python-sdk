import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Literal

from pydantic import AnyUrl, BaseModel

from src.generated.model import (
    ConversationCreateConversationRequest,
    ConversationCreateConversationResponse,
    ConversationGenerateConversationStarterRequest,
    ConversationGenerateConversationStarterResponse,
    ConversationGetConversationMessagesResponse,
    ConversationGetConversationsResponse,
    ConversationGetInteractionInsightsResponse,
    ConversationInteractWithConversationResponse,
    ConversationRecommendResponsesForInteractionResponse,
    CreateConversationParametersQuery,
    GetConversationMessagesParametersQuery,
    GetConversationsParametersQuery,
    InteractWithConversationParametersQuery,
)
from src.http_client import AmigoHttpClient


class GetMessageSourceResponse(BaseModel):
    """
    Response model for the `get_message_source` endpoint.
    TODO: Remove once the OpenAPI spec contains the correct response model for this endpoint.
    """

    url: AnyUrl
    expires_at: datetime
    content_type: Literal["audio/mpeg", "audio/wav"]


class ConversationResource:
    """Conversation resource for Amigo API operations."""

    def __init__(self, http_client: AmigoHttpClient, organization_id: str) -> None:
        self._http = http_client
        self._organization_id = organization_id

    async def create_conversation(
        self,
        body: ConversationCreateConversationRequest,
        params: CreateConversationParametersQuery,
        abort_event: asyncio.Event | None = None,
    ) -> "AsyncGenerator[ConversationCreateConversationResponse, None]":
        """Create a new conversation and stream NDJSON events.

        Returns an async generator yielding `ConversationCreateConversationResponse` events.
        """

        async def _generator():
            async for line in self._http.stream_lines(
                "POST",
                f"/v1/{self._organization_id}/conversation/",
                params=params.model_dump(mode="json", exclude_none=True),
                json=body.model_dump(mode="json", exclude_none=True),
                abort_event=abort_event,
            ):
                # Each line is a JSON object representing a discriminated union event
                yield ConversationCreateConversationResponse.model_validate_json(line)

        return _generator()

    async def interact_with_conversation(
        self,
        conversation_id: str,
        body: Any,
        params: InteractWithConversationParametersQuery,
        abort_event: asyncio.Event | None = None,
    ) -> "AsyncGenerator[ConversationInteractWithConversationResponse, None]":
        """Interact with a conversation and stream NDJSON events.

        Returns an async generator yielding `ConversationInteractWithConversationResponse` events.
        """

        async def _generator():
            async for line in self._http.stream_lines(
                "POST",
                f"/v1/{self._organization_id}/conversation/{conversation_id}/interact",
                params=params.model_dump(mode="json", exclude_none=True),
                json=body,
                abort_event=abort_event,
            ):
                # Each line is a JSON object representing a discriminated union event
                yield ConversationInteractWithConversationResponse.model_validate_json(
                    line
                )

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
            params=params.model_dump(mode="json", exclude_none=True),
        )
        return ConversationGetConversationMessagesResponse.model_validate_json(
            response.text
        )

    async def recommend_responses_for_interaction(
        self, conversation_id: str, interaction_id: str
    ) -> ConversationRecommendResponsesForInteractionResponse:
        """Recommend responses for an interaction."""
        response = await self._http.request(
            "GET",
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
