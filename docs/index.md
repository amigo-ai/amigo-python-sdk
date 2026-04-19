# Amigo Python SDK

Official Python SDK for the classic Amigo API.

## Status

This SDK remains supported for current classic API integrations. The Platform API is the long-term direction for new workspace-scoped capabilities, and Amigo will publish a migration path for Python customers before recommending a move. Existing classic integrations are not end-of-life.

## Highlights

- Async and sync clients: `AsyncAmigoClient` and `AmigoClient`
- Automatic authentication with token refresh
- NDJSON streaming helpers for conversation endpoints
- Pydantic v2 models generated from the OpenAPI schema

## Quick Start

```python
from amigo_sdk import AmigoClient

with AmigoClient() as client:
    org = client.organizations.get()
    print(org.id)
```

## Reference

- [Client](reference/client.md)
- [Resources](reference/resources.md)
- [Models](reference/models.md)
- [Errors](reference/errors.md)
- [Configuration](reference/config.md)
