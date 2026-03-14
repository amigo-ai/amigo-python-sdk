#!/usr/bin/env python3
"""Generate changelog entries from git log between tags."""

import argparse
import re
import subprocess
from datetime import date

CATEGORIES = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "perf": "Performance",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "test": "Tests",
    "ci": "CI",
    "chore": "Chores",
}

CATEGORY_ORDER = ["feat", "fix", "perf", "refactor", "docs", "test", "ci", "chore"]


def get_last_tag() -> str:
    result = subprocess.run(
        ["git", "tag", "--sort=-v:refname"],
        capture_output=True,
        text=True,
        check=True,
    )
    tags = result.stdout.strip().split("\n")
    return tags[0] if tags and tags[0] else ""


def get_repo_url() -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
    )
    url = result.stdout.strip().removesuffix(".git")
    return re.sub(r"git@github\.com:", "https://github.com/", url)


def get_commits(from_ref: str, to_ref: str) -> list[str]:
    result = subprocess.run(
        ["git", "log", f"{from_ref}..{to_ref}", "--oneline", "--format=%s"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.strip().split("\n") if line]


def categorize(commits: list[str]) -> dict[str, list[str]]:
    categorized: dict[str, list[str]] = {k: [] for k in CATEGORIES}
    uncategorized: list[str] = []
    for msg in commits:
        matched = False
        for prefix in CATEGORIES:
            if msg.startswith(f"{prefix}:") or msg.startswith(f"{prefix}("):
                clean = re.sub(rf"^{prefix}(\([^)]*\))?:\s*", "", msg)
                categorized[prefix].append(clean)
                matched = True
                break
        if not matched:
            uncategorized.append(msg)
    if uncategorized:
        categorized["other"] = uncategorized
    return categorized


def format_entry(msg: str, repo_url: str) -> str:
    pr_match = re.search(r"#(\d+)", msg)
    if pr_match:
        pr_num = pr_match.group(1)
        msg = msg.replace(f"#{pr_num}", f"[#{pr_num}]({repo_url}/pull/{pr_num})")
    return f"- {msg}"


def main():
    parser = argparse.ArgumentParser(description="Generate changelog from git log")
    parser.add_argument(
        "--from-tag", default=None, help="Start tag (default: last tag)"
    )
    parser.add_argument("--to-ref", default="HEAD", help="End ref (default: HEAD)")
    parser.add_argument(
        "--version", default="Unreleased", help="Version label (default: Unreleased)"
    )
    args = parser.parse_args()

    from_tag = args.from_tag or get_last_tag()
    if not from_tag:
        result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        from_tag = result.stdout.strip()

    repo_url = get_repo_url()
    commits = get_commits(from_tag, args.to_ref)
    categorized = categorize(commits)
    today = date.today().isoformat()

    print(f"## [{args.version}] - {today}\n")
    all_categories = {**{k: CATEGORIES[k] for k in CATEGORY_ORDER}, "other": "Other"}
    for prefix, title in all_categories.items():
        entries = categorized.get(prefix, [])
        if entries:
            print(f"### {title}")
            for msg in entries:
                print(format_entry(msg, repo_url))
            print()


if __name__ == "__main__":
    main()
