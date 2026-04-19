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

- `check` runs formatting, linting, and tests
- `check --fix` auto-fixes what it can, then reruns checks
- `check --fast` runs the fast path without tests

### Codegen And Docs

- `gen-models` regenerates models from the API schema
- `mkdocs build --strict` builds the docs site

## Testing

Pytest is the test runner.

```bash
pytest
pytest -m integration
pytest --cov=src
```

Integration tests require valid Amigo API credentials in the environment.

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

1. Run `check --fix`
2. Run `pytest`
3. Rebuild generated models if the API contract changed
4. Update README or docs if customer-visible behavior changed

## Release Notes

Releases are handled in GitHub Actions. If your change affects package behavior, public docs, or generated models, include enough context in the PR description for maintainers to produce accurate release notes.
