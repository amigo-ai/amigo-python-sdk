# Amigo Python SDK — Examples

This folder contains small, readable examples for consuming the Amigo Python SDK.

All examples share an amigo_sdk dependency installation from PyPI via `examples/requirements.txt`.

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install shared dependencies (SDK from PyPI):
   ```bash
   pip install -r examples/requirements.txt
   ```

## Examples

### Conversation (`examples/conversation`)

- Create a conversation
- Send a text interaction and stream events
- Fetch recent messages
- Finish the conversation

Setup for this example:

1. Copy `examples/.env.example` to `examples/.env` and fill in values (shared across examples):
   ```bash
   cp examples/.env.example examples/.env
   ```
2. Run the example:
   ```bash
   python examples/conversation/conversation.py
   ```

Required environment variables (loaded via `python-dotenv` from `examples/.env`):

- `AMIGO_API_KEY`
- `AMIGO_API_KEY_ID`
- `AMIGO_USER_ID`
- `AMIGO_ORGANIZATION_ID`
- `AMIGO_SERVICE_ID` (required)
- `AMIGO_BASE_URL` (optional)

Notes:

- Errors like conflict/not-found during finish are tolerated due to eventual consistency.
- Examples prioritize simplicity and clarity for easy replication.
