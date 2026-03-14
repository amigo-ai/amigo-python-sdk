# Amigo Python SDK

Python client library for the Amigo AI API with both async and sync support.

- **Async and sync clients** — `AsyncAmigoClient` and `AmigoClient`
- **Automatic authentication** — API key exchange with proactive token refresh
- **NDJSON streaming** — Async generators for conversation endpoints
- **Type safety** — Pydantic v2 models generated from OpenAPI spec

## Quick Start

```python
from amigo_sdk import AmigoClient

client = AmigoClient()
org = client.organizations.get_organization()
```

## API Reference

- [Client](reference/client.md) — `AmigoClient` and `AsyncAmigoClient`
- [Resources](reference/resources.md) — Conversation, User, Organization, Service
- [Models](reference/models.md) — Request/response Pydantic models
- [Errors](reference/errors.md) — Error hierarchy and handling
- [Configuration](reference/config.md) — `AmigoConfig` and environment variables
