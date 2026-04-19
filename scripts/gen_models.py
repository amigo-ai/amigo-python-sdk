import argparse
import json
from pathlib import Path

from datamodel_code_generator import (
    DataModelType,
    InputFileType,
    OpenAPIScope,
    generate,
)

# Prefixes to strip from schema names (API-specific internal paths)
STRIP_PREFIXES = [
    "src__app__endpoints__",
    "src__app__amigo__",
    "amigo_lib__",
]

# The live classic API can omit org-branding fields even though the published
# OpenAPI snapshot still marks them required. Relax them after generation so
# released SDK models match the payloads customers actually receive.
ORGANIZATION_RESPONSE_COMPAT_FIXES = {
    "    title: str = Field(\n        ...,": "    title: str | None = Field(\n        None,",
    "    main_description: str = Field(\n        ...,": "    main_description: str | None = Field(\n        None,",
    "    sub_description: str = Field(\n        ...,": "    sub_description: str | None = Field(\n        None,",
    "    onboarding_instructions: list[str] = Field(\n        ...,": "    onboarding_instructions: list[str] | None = Field(\n        None,",
}


def strip_prefixes_from_schema(spec: dict) -> dict:
    """
    Pre-process the OpenAPI spec to strip internal prefixes from schema names.
    This allows the code generator's built-in name sanitization to work correctly.
    """
    schemas = spec.get("components", {}).get("schemas", {})
    if not schemas:
        return spec

    rename_map: dict[str, str] = {}
    for name in schemas:
        new_name = name
        for prefix in STRIP_PREFIXES:
            if new_name.startswith(prefix):
                new_name = new_name[len(prefix) :]
                break
        if new_name != name:
            rename_map[name] = new_name

    if not rename_map:
        return spec

    new_schemas = {}
    for name, schema in schemas.items():
        new_name = rename_map.get(name, name)
        new_schemas[new_name] = schema
    spec["components"]["schemas"] = new_schemas

    def update_refs(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                for old, new in rename_map.items():
                    old_ref = f"#/components/schemas/{old}"
                    new_ref = f"#/components/schemas/{new}"
                    if ref == old_ref:
                        obj["$ref"] = new_ref
                        break
            for value in obj.values():
                update_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                update_refs(item)

    update_refs(spec)
    return spec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Python models from the committed classic OpenAPI snapshot."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        help="Path to an OpenAPI JSON document. Defaults to specs/openapi-baseline.json.",
    )
    return parser.parse_args()


def resolve_spec_path(root: Path, spec_arg: Path | None) -> Path:
    if spec_arg is not None:
        return spec_arg.expanduser().resolve()

    default_spec = root / "specs" / "openapi-baseline.json"
    if default_spec.exists():
        return default_spec

    raise FileNotFoundError(
        "No committed OpenAPI snapshot found at specs/openapi-baseline.json. Run `sync-openapi` first."
    )


def load_spec(spec_path: Path) -> dict:
    spec = json.loads(spec_path.read_text())
    if not isinstance(spec, dict) or not isinstance(spec.get("openapi"), str):
        raise ValueError(f"Invalid OpenAPI document: {spec_path}")
    return spec


def apply_output_compat_fixes(output_file: Path) -> None:
    text = output_file.read_text()
    for old, new in ORGANIZATION_RESPONSE_COMPAT_FIXES.items():
        if old not in text:
            raise RuntimeError(
                f"Unable to apply generated-model compatibility fix for pattern: {old}"
            )
        text = text.replace(old, new, 1)
    output_file.write_text(text)


def main() -> None:
    args = parse_args()
    root = Path(__file__).parent.parent
    spec_path = resolve_spec_path(root, args.spec)
    out_dir = root / "src" / "amigo_sdk" / "generated"
    output_file = out_dir / "model.py"
    aliases_path = root / "scripts" / "aliases.json"

    out_dir.mkdir(parents=True, exist_ok=True)

    if output_file.exists():
        output_file.unlink()

    print(f"Generating models from {spec_path}...")
    spec = strip_prefixes_from_schema(load_spec(spec_path))

    aliases: dict[str, str] = {}
    if aliases_path.exists():
        aliases = json.loads(aliases_path.read_text())

    generate(
        json.dumps(spec),
        input_file_type=InputFileType.OpenAPI,
        output=output_file,
        output_model_type=DataModelType.PydanticV2BaseModel,
        openapi_scopes=[
            OpenAPIScope.Schemas,
            OpenAPIScope.Parameters,
            OpenAPIScope.Paths,
            OpenAPIScope.Tags,
        ],
        snake_case_field=True,
        field_constraints=True,
        use_operation_id_as_name=True,
        reuse_model=True,
        aliases=aliases,
        collapse_root_models=False,
    )
    apply_output_compat_fixes(output_file)

    print(f"Generated models from {spec_path} -> {output_file}")


if __name__ == "__main__":
    main()
