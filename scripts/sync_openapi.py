import argparse
import json
from pathlib import Path

import httpx

DEFAULT_SCHEMA_URL = "https://api.amigo.ai/v1/openapi.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh the committed classic OpenAPI snapshot."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_SCHEMA_URL,
        help="OpenAPI URL to fetch. Defaults to the classic Amigo API schema URL.",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        help="Path to a local OpenAPI JSON file to copy into specs/openapi-baseline.json.",
    )
    return parser.parse_args()


def load_document(args: argparse.Namespace) -> dict:
    if args.spec is not None:
        spec_path = args.spec.expanduser().resolve()
        print(f"Syncing OpenAPI snapshot from file: {spec_path}")
        document = json.loads(spec_path.read_text())
    else:
        print(f"Syncing OpenAPI snapshot from URL: {args.url}")
        response = httpx.get(args.url, timeout=30.0)
        response.raise_for_status()
        document = response.json()

    if not isinstance(document, dict) or not isinstance(document.get("openapi"), str):
        raise ValueError("Invalid OpenAPI document received while syncing snapshot.")

    return document


def main() -> None:
    args = parse_args()
    root = Path(__file__).parent.parent
    out_path = root / "specs" / "openapi-baseline.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    document = load_document(args)
    out_path.write_text(f"{json.dumps(document, indent=2)}\n")

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
