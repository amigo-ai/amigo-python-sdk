# Contributing Guide

## Quick Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the project in development mode
pip install -e ".[dev]"
```

## Development Commands

```bash
check                     # Run all checks (format, lint, tests)
check --fix               # Auto-fix issues and run all checks
check --fast              # Format + lint only (skip tests)

gen-models                # Generate models from API spec
```

## Workflow

1. **Before committing:** Run `check --fix` to auto-fix issues
2. **During development:** Use `check --fast` for quick validation
3. **Update models:** Run `gen-models` when API changes

## IDE Setup (VS Code)

Install extensions:

- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

Settings are pre-configured in `.vscode/settings.json`.

## Troubleshooting

- **Command not found:** Activate virtual environment with `source .venv/bin/activate`
- **Linting failures:** Run `check --fix` to auto-fix issues
- **Model import errors:** Run `gen-models` to regenerate models
