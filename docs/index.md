# Amigo Python SDK

Python client library for the classic Amigo API.

## Status

This SDK remains supported for current classic API integrations. The Platform API is the long-term direction for new workspace-scoped capabilities, and Amigo will publish a migration path for Python customers before recommending a move.

## Highlights

- Sync and async clients: `AmigoClient` and `AsyncAmigoClient`
- Automatic authentication and token refresh
- Generated Pydantic models from the OpenAPI schema
- NDJSON streaming helpers for conversation endpoints

## Quick Start

```python
from amigo_sdk import AmigoClient

with AmigoClient() as client:
    organization = client.organizations.get()
    print(organization.id)
```

## Reference

- [Client](reference/client.md)
- [Resources](reference/resources.md)
- [Models](reference/models.md)
- [Errors](reference/errors.md)
- [Configuration](reference/config.md)
