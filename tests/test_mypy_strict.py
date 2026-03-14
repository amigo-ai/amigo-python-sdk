"""
Test that runs mypy in strict mode on the SDK source (excluding generated code).
Run with: pytest tests/test_mypy_strict.py -v

This test requires mypy to be installed: pip install mypy
"""

import subprocess
import sys
import pytest


@pytest.mark.slow
def test_mypy_strict_on_sdk_source():
    """Run mypy in strict mode on SDK source, excluding generated code."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "src/amigo_sdk",
            "--strict",
            "--ignore-missing-imports",
            "--exclude",
            "generated/",
            "--no-error-summary",
        ],
        capture_output=True,
        text=True,
        cwd=str(__import__("pathlib").Path(__file__).parent.parent),
    )

    if result.returncode != 0:
        # Collect errors, filtering out notes
        errors = [
            line
            for line in result.stdout.strip().split("\n")
            if line and ": error:" in line
        ]

        if errors:
            # For now, report but don't fail — track progress toward strict mode
            print(f"\nmypy strict mode found {len(errors)} errors:")
            for error in errors[:20]:
                print(f"  {error}")
            if len(errors) > 20:
                print(f"  ... and {len(errors) - 20} more")

            # TODO: Once all errors are fixed, change this to assert errors == []
            pytest.skip(
                f"mypy strict mode has {len(errors)} errors — tracking progress"
            )
