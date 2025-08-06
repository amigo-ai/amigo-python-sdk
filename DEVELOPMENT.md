# Development Guide

This guide helps you set up a smooth development workflow with manual quality checks.

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the project in development mode
pip install -e ".[dev]"
```

### 2. Available Commands

```bash
# Quality checks
check                     # Run all checks (format, lint, tests)
check --fix               # Run all checks and auto-fix issues
check --fast              # Run format + lint only (skip tests)

# Individual commands
ruff check .              # Check for linting issues
ruff check . --fix        # Fix auto-fixable linting issues
ruff format .             # Format code
ruff format --check .     # Check if code is formatted correctly
pytest                    # Run tests (unit tests only)
pytest --cov=src --cov-report=xml --cov-report=term  # Run tests with coverage

# Generate models (if needed)
gen-models                # Generate Pydantic models from API spec
```

## 🛠 IDE/Editor Setup for Automatic Linting & Formatting

### VS Code Setup

1. **Install Extensions:**

   - [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
   - [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

2. **Settings are already configured in `.vscode/settings.json`** ✅

## 📋 Development Workflow

### Before Committing

Run the check script to ensure your code is ready:

```bash
# Quick check (format + lint only)
check --fast

# Full check with tests
check

# Auto-fix issues and run full check
check --fix
```

### During Development

- **Auto-fix on save** (if you set up your IDE correctly)
- **Run tests frequently:** `pytest`
- **Check coverage:** `pytest --cov=src`
- **Quick validation:** `check --fast`

## 🔍 Check Script Options

The `check` script gives you flexible control:

### **Full Check (Default)**

```bash
check
```

- ✅ Format check
- ✅ Lint check
- ✅ Run tests with coverage

### **Auto-fix Mode**

```bash
check --fix
```

- 🔧 Format code automatically
- 🔧 Fix linting issues automatically
- ✅ Run tests with coverage

### **Fast Mode**

```bash
check --fast
```

- ✅ Format check
- ✅ Lint check
- ⏭️ Skip tests (for quick validation)

### **Combine Options**

```bash
check --fix --fast    # Auto-fix format/lint, skip tests
```

## 🐛 Troubleshooting

### "Command not found" errors

Make sure your virtual environment is activated:

```bash
source .venv/bin/activate
```

### Linting failures

Run the check script to see what's wrong:

```bash
check                 # See what's failing
check --fix           # Auto-fix what's possible
```

### Import sorting issues

Ruff handles import sorting automatically:

```bash
check --fix  # This will reorganize imports
```

## 📊 Coverage Reports

After running tests with coverage, you can view detailed coverage reports:

- **Terminal:** Coverage summary is displayed
- **HTML:** Open `htmlcov/index.html` in your browser
- **XML:** `coverage.xml` for CI systems

## 🎯 CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/test.yml`) runs:

1. **Setup:** Python 3.13, install dependencies
2. **Lint:** `ruff check .`
3. **Format check:** `ruff format --check .`
4. **Tests:** `pytest --cov=src --cov-report=xml`
5. **Coverage:** Upload to Codecov

Match this locally with:

```bash
check  # Runs the same checks as CI
```

## 🚀 Quick Commands

### One-liner for CI checks:

```bash
check
```

### Fix everything automatically:

```bash
check --fix
```

### Quick validation during development:

```bash
check --fast
```

### Full development setup from scratch:

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
```

## 💡 Pro Tips

- **Use `check --fast`** during active development for quick feedback
- **Use `check --fix`** before committing to auto-fix issues
- **Use `check`** (full) before pushing to ensure everything passes CI
- **IDE auto-formatting** handles most formatting automatically
- **VS Code settings** already configured for optimal workflow
