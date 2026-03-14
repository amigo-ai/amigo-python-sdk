"""Public model re-exports from generated OpenAPI types.

Only models used by SDK resource methods and commonly needed by consumers
are exported here. For the full set, import from amigo_sdk.generated.model.
"""

from .generated.model import (
    # Conversation
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
    Format,
    GetConversationMessagesParametersQuery,
    GetConversationsParametersQuery,
    # Service
    GetServicesParametersQuery,
    # User
    GetUsersParametersQuery,
    InteractWithConversationParametersQuery,
    # Organization
    OrganizationGetOrganizationResponse,
    ServiceGetServicesResponse,
    UserCreateInvitedUserRequest,
    UserCreateInvitedUserResponse,
    UserGetUserModelResponse,
    UserGetUsersResponse,
    # Auth
    UserSignInWithApiKeyResponse,
    UserUpdateUserInfoRequest,
)

__all__ = [
    # Auth
    "UserSignInWithApiKeyResponse",
    # Conversation
    "ConversationCreateConversationRequest",
    "ConversationCreateConversationResponse",
    "ConversationGenerateConversationStarterRequest",
    "ConversationGenerateConversationStarterResponse",
    "ConversationGetConversationMessagesResponse",
    "ConversationGetConversationsResponse",
    "ConversationGetInteractionInsightsResponse",
    "ConversationInteractWithConversationResponse",
    "ConversationRecommendResponsesForInteractionResponse",
    "CreateConversationParametersQuery",
    "GetConversationMessagesParametersQuery",
    "GetConversationsParametersQuery",
    "InteractWithConversationParametersQuery",
    "Format",
    # Organization
    "OrganizationGetOrganizationResponse",
    # Service
    "GetServicesParametersQuery",
    "ServiceGetServicesResponse",
    # User
    "GetUsersParametersQuery",
    "UserCreateInvitedUserRequest",
    "UserCreateInvitedUserResponse",
    "UserGetUserModelResponse",
    "UserGetUsersResponse",
    "UserUpdateUserInfoRequest",
]
