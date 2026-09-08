# Contributing to Amigo Python SDK

Thank you for contributing to `amigo_sdk`. This repository is the public Python client for the classic Amigo API, and contributor changes should keep that customer surface reliable and well-documented while platform migration work is planned.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Commands

### Validation

- `python scripts/check.py` runs formatting, linting, and tests
- `python scripts/check.py --fix` auto-fixes what it can, then reruns checks
- `python scripts/check.py --fast` runs the fast path without tests

### Codegen And Docs

- `python scripts/gen_models.py` regenerates models from the committed `specs/openapi-baseline.json` snapshot
- `python scripts/sync_openapi.py` refreshes `specs/openapi-baseline.json` from the live classic API before regeneration
- Install docs dependencies with `pip install -e ".[docs]"`, then `mkdocs build --strict` builds the docs site

## Testing

Pytest is the test runner.

```bash
python -m pytest
python -m pytest -m integration
python -m pytest --cov=src
```

Integration tests require valid Amigo API credentials in the environment. Unit tests use mocked requests. Run `mypy src/amigo_sdk/ --ignore-missing-imports` as well; it is a required CI check. Development scripts run from this checkout and are not commands installed by the public wheel.

## Project Structure

```text
src/amigo_sdk/
├── generated/      # generated models and schema-derived code
├── resources/      # resource clients
├── sdk_client.py   # sync and async clients
└── webhooks.py     # webhook helpers

docs/
├── index.md
└── reference/

examples/
└── conversation/
```

## Pull Requests

Before opening a PR:

1. Run `python scripts/check.py --fix`
2. Run `python -m pytest`
3. Run `python scripts/sync_openapi.py` and `python scripts/gen_models.py` if the API contract changed
4. Update README or docs if customer-visible behavior changed

## Release Notes

Releases are handled in GitHub Actions. If your change affects package behavior, public docs, or generated models, include enough context in the PR description for maintainers to produce accurate release notes.
