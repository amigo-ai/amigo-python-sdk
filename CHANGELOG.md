# Changelog

All notable changes to the Amigo Python SDK will be documented in this file.

This project follows [Semantic Versioning](https://semver.org/) and the format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [1.0.0rc1] - 2026-03-14

### Breaking Changes

- **Renamed `PermissionError` to `ForbiddenError`**: avoids shadowing Python's builtin `PermissionError` (#30)
- **Renamed sync `aclose()` to `close()`**: sync `AmigoClient` and `AmigoHttpClient` now use `close()` (async keeps `aclose()`) (#30)
- **Normalized resource properties to plural**: `client.organization` → `client.organizations`, `client.service` → `client.services`, `client.conversation` → `client.conversations` (#30)

### Added

- **AgentResource**: `create_agent`, `get_agents`, `delete_agent`, `create_agent_version`, `get_agent_versions` with `list/create/delete` aliases (async + sync) (#30)
- **ContextGraphResource**: `create_context_graph`, `get_context_graphs`, `create_context_graph_version`, `delete_context_graph`, `get_context_graph_versions` with `list/create/delete` aliases (async + sync) (#30)
- **ServiceResource extended**: `create_service`, `update_service`, `upsert_version_set`, `delete_version_set` with `list/create` aliases (#30)
- **Convenience aliases on all resources**: UserResource (`list`, `create`, `delete`, `update`, `get_model`), ConversationResource (`list`, `create`, `interact`, `finish`, `messages`), ServiceResource (`list`) (#30)
- **Exports from `__init__.py`**: `AmigoConfig`, all error classes (`ForbiddenError`, `BadRequestError`, etc.), `SDKInternalError` (#30)
- **`mypy`** added to dev dependencies (#30)
- **Project URLs** added to pyproject.toml (Homepage, Docs, Repository, Issues, Changelog) (#30)
- **License field** (`MIT`) added to pyproject.toml (#30)
- Webhook type safety: frozen dataclasses for all webhook event types, `parse_webhook_event()` with HMAC-SHA256 verification, replay protection (#26)
- Rate limit header exposure: `RateLimitInfo` dataclass, `parse_rate_limit_headers()` utility (#26)
- Changelog automation: `scripts/generate_changelog.py` wired into release workflow (#25)
- Performance benchmarks: token refresh latency, async concurrent request handling (#27)
- SECURITY.md with responsible disclosure policy
- CODE_OF_CONDUCT.md
- GitHub issue and PR templates

### Fixed

- Streaming read timeout: set to 300s for agent responses (was httpx default 5s) (#28)
- Dependabot alert #1: `black` arbitrary file write CVE (#23)
- CodeQL workflow conflict with GitHub default setup (#28)
- Integration test 409 Conflict: added retry with cleanup for sync test class (#28)

### Removed

- **`scripts/` from wheel build**: no longer shipped in published package (#30)

## [0.136.0] - 2026-03-14

- Auto-generated model updates from OpenAPI spec

## [0.135.0] - 2026-03-13

- Auto-generated model updates from OpenAPI spec

## [0.134.0] - 2026-03-12

- Auto-generated model updates from OpenAPI spec

---

> **Note**: Earlier versions were auto-released from OpenAPI spec changes. See [GitHub Releases](https://github.com/amigo-ai/amigo-python-sdk/releases) for the full history.
