# Changelog

All notable changes to the Amigo Python SDK will be documented in this file.

This project follows [Semantic Versioning](https://semver.org/) and the format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Webhook type safety: frozen dataclasses for all webhook event types, `parse_webhook_event()` with HMAC-SHA256 verification, replay protection (#26)
- Rate limit header exposure: `RateLimitInfo` dataclass, `parse_rate_limit_headers()` utility (#26)
- Changelog automation: `scripts/generate_changelog.py` wired into release workflow (#25)
- Performance benchmarks: token refresh latency, async concurrent request handling (#27)
- SECURITY.md with responsible disclosure policy
- CHANGELOG.md
- CODE_OF_CONDUCT.md
- GitHub issue and PR templates
- Troubleshooting section in README

### Fixed

- Streaming read timeout: set to 300s for agent responses (was httpx default 5s) (#28)
- Dependabot alert #1: `black` arbitrary file write CVE (#23)
- CodeQL workflow conflict with GitHub default setup (#28)
- Integration test 409 Conflict: added retry with cleanup for sync test class (#28)

## [0.136.0] - 2026-03-14

- Auto-generated model updates from OpenAPI spec

## [0.135.0] - 2026-03-13

- Auto-generated model updates from OpenAPI spec

## [0.134.0] - 2026-03-12

- Auto-generated model updates from OpenAPI spec

---

> **Note**: Earlier versions were auto-released from OpenAPI spec changes. See [GitHub Releases](https://github.com/amigo-ai/amigo-python-sdk/releases) for the full history.
