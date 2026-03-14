Verify the SDK is ready for release:
1. Run `ruff check src/ tests/` - must pass
2. Run `ruff format --check src/ tests/` - must pass
3. Run `pytest` - all tests must pass
4. Check CHANGELOG.md has entries for unreleased changes
5. Verify version in src/amigo_sdk/__init__.py
6. Report any blockers for release
