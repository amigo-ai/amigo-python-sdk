import pytest

from amigo_sdk.config import AmigoConfig
from amigo_sdk.http_client import AmigoSyncHttpClient
from amigo_sdk.resources.conversation import SyncConversationResource


@pytest.fixture
def mock_config() -> AmigoConfig:
    return AmigoConfig(
        api_key="test-api-key",
        api_key_id="test-api-key-id",
        user_id="test-user-id",
        organization_id="org-1",
        base_url="https://api.example.com",
    )


@pytest.fixture
def conversation_resource(mock_config: AmigoConfig) -> SyncConversationResource:
    http_client = AmigoSyncHttpClient(mock_config)
    return SyncConversationResource(http_client, mock_config.organization_id)


@pytest.mark.unit
class TestSyncConversationResourceUnit:
    def test_get_conversations_returns_data_and_passes_query_params(
        self, conversation_resource: SyncConversationResource, monkeypatch
    ) -> None:
        from amigo_sdk.generated.model import GetConversationsParametersQuery

        called = {}

        def fake_request(method, path, **kwargs):  # noqa: ANN001
            class R:
                status_code = 200
                text = '{"conversations": [], "has_more": false, "continuation_token": null}'

            called["method"] = method
            called["path"] = path
            called.update(kwargs)
            return R()

        monkeypatch.setattr(conversation_resource._http, "request", fake_request)

        params = GetConversationsParametersQuery(limit=10)
        data = conversation_resource.get_conversations(params)
        assert data.has_more is False
        assert called["method"] == "GET"
        assert called["path"].endswith("/v1/org-1/conversation/")
        assert called["params"]["limit"] == 10
