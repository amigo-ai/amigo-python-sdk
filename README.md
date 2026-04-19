# amigo_sdk

[![Tests](https://github.com/amigo-ai/amigo-python-sdk/actions/workflows/test.yml/badge.svg)](https://github.com/amigo-ai/amigo-python-sdk/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/amigo-ai/amigo-python-sdk/graph/badge.svg?token=1A7KVPV9ZR)](https://codecov.io/gh/amigo-ai/amigo-python-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for the Amigo API.

This repository provides synchronous and asynchronous Python clients for the classic org-scoped Amigo API, with generated Pydantic models, typed errors, and NDJSON conversation streaming.

## Documentation

- [Product Docs](https://docs.amigo.ai)
- [Developer Guide](https://docs.amigo.ai/developer-guide)
- [Repo Docs](https://github.com/amigo-ai/amigo-python-sdk/blob/main/docs/index.md)
- [Examples](https://github.com/amigo-ai/amigo-python-sdk/tree/main/examples)
- [Changelog](https://github.com/amigo-ai/amigo-python-sdk/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/amigo-ai/amigo-python-sdk/blob/main/CONTRIBUTING.md)

## Status

This package remains the supported Python SDK for the classic Amigo API. The Platform API is the long-term direction for new workspace-scoped capabilities, but classic Python customers are not facing an abrupt end-of-life event. As equivalent platform surfaces become available, Amigo will publish a migration path and upgrade guidance before asking customers to move.

Existing classic integrations can continue to use `amigo_sdk` while that migration path is rolled out.

## Choose The Right Surface

| If you need | Start here |
| --- | --- |
| The current org-scoped Amigo API from Python | `amigo_sdk` |
| New workspace-scoped Platform API capabilities | [Platform API docs](https://docs.amigo.ai/api-reference) today. Migration guidance for Python customers will follow as platform-native coverage expands |

## Installation

Python `3.11+` is required.

```bash
pip install amigo_sdk
```

## Quick Start

### Sync Client

```python
from amigo_sdk import AmigoClient
from amigo_sdk.models import GetConversationsParametersQuery

with AmigoClient(
    api_key="your-api-key",
    api_key_id="your-api-key-id",
    user_id="user-id",
    organization_id="your-organization-id",
) as client:
    conversations = client.conversations.get_conversations(
        GetConversationsParametersQuery(limit=10, sort_by=["-created_at"])
    )
    print(conversations.conversations[0].id if conversations.conversations else None)
```

### Async Client

```python
import asyncio

from amigo_sdk import AsyncAmigoClient
from amigo_sdk.models import GetConversationsParametersQuery


async def main() -> None:
    async with AsyncAmigoClient(
        api_key="your-api-key",
        api_key_id="your-api-key-id",
        user_id="user-id",
        organization_id="your-organization-id",
    ) as client:
        conversations = await client.conversations.get_conversations(
            GetConversationsParametersQuery(limit=10, sort_by=["-created_at"])
        )
        print(len(conversations.conversations))


asyncio.run(main())
```

## Configuration

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `api_key` | `str` | Yes | API key from the Amigo dashboard |
| `api_key_id` | `str` | Yes | API key ID paired with `api_key` |
| `user_id` | `str` | Yes | User ID on whose behalf the request is made |
| `organization_id` | `str` | Yes | Organization ID for the classic API |
| `base_url` | `str` | No | Override the API base URL. Defaults to `https://api.amigo.ai` |

Environment variables are also supported:

```bash
export AMIGO_API_KEY="your-api-key"
export AMIGO_API_KEY_ID="your-api-key-id"
export AMIGO_USER_ID="user-id"
export AMIGO_ORGANIZATION_ID="your-organization-id"
export AMIGO_BASE_URL="https://api.amigo.ai"
```

## What This SDK Covers

- Conversations and streaming interaction events
- Organizations, services, users, agents, and context graphs
- Sync and async client APIs
- Generated Pydantic request and response models
- Typed errors and rate-limit helpers

## Generated Models

The SDK ships with generated Pydantic models and exposes them from `amigo_sdk.models`:

```python
from amigo_sdk.models import (
    ConversationCreateConversationRequest,
    GetConversationsParametersQuery,
)
```

## Error Handling

```python
from amigo_sdk import AmigoClient
from amigo_sdk.errors import AuthenticationError, NotFoundError, RateLimitError

try:
    with AmigoClient() as client:
        organization = client.organizations.get()
        print(organization.id)
except AuthenticationError as error:
    print("Authentication failed:", error)
except NotFoundError as error:
    print("Resource not found:", error)
except RateLimitError as error:
    print("Rate limited:", error)
```

## Support

Use the [issue tracker](https://github.com/amigo-ai/amigo-python-sdk/issues) for bugs and feature requests. For vulnerability reports, see [SECURITY.md](https://github.com/amigo-ai/amigo-python-sdk/blob/main/SECURITY.md).
