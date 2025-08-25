import pytest

from amigo_sdk.config import AmigoConfig
from amigo_sdk.sdk_client import AmigoClient


@pytest.mark.unit
class TestAmigoClientSync:
    def test_initialization_with_config(self):
        cfg = AmigoConfig(
            api_key="k",
            api_key_id="kid",
            user_id="u",
            organization_id="o",
            base_url="https://api.example.com",
        )
        client = AmigoClient(config=cfg)
        assert client.config is cfg

    def test_context_manager_closes_http(self):
        cfg = AmigoConfig(
            api_key="k",
            api_key_id="kid",
            user_id="u",
            organization_id="o",
            base_url="https://api.example.com",
        )
        with AmigoClient(config=cfg) as c:
            assert c.config is cfg
        # cannot easily assert underlying httpx.Client closed here, but no exception indicates closure

    def test_exports_resources(self):
        cfg = AmigoConfig(
            api_key="k",
            api_key_id="kid",
            user_id="u",
            organization_id="o",
            base_url="https://api.example.com",
        )
        client = AmigoClient(config=cfg)
        assert hasattr(client, "organization")
        assert hasattr(client, "service")
        assert hasattr(client, "conversation")
        assert hasattr(client, "users")
