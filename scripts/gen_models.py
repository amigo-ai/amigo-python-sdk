import json
from pathlib import Path

import httpx
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


def strip_prefixes_from_schema(spec: dict) -> dict:
    """
    Pre-process the OpenAPI spec to strip internal prefixes from schema names.
    This allows the code generator's built-in name sanitization to work correctly.
    """
    schemas = spec.get("components", {}).get("schemas", {})
    if not schemas:
        return spec

    # Build a mapping of old names to new names
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

    # Rename schemas
    new_schemas = {}
    for name, schema in schemas.items():
        new_name = rename_map.get(name, name)
        new_schemas[new_name] = schema
    spec["components"]["schemas"] = new_schemas

    # Update all $ref pointers throughout the spec
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


def main() -> None:
    schema_url = "https://api.amigo.ai/v1/openapi.json"
    root = Path(__file__).parent.parent
    out_dir = root / "src" / "amigo_sdk" / "generated"
    output_file = out_dir / "model.py"
    aliases_path = root / "scripts" / "aliases.json"

    # Create the generated directory if it doesn't exist
    out_dir.mkdir(parents=True, exist_ok=True)

    # Remove existing model.py if it exists
    if output_file.exists():
        output_file.unlink()

    # Fetch the OpenAPI schema from the remote URL
    print(f"Fetching OpenAPI schema from {schema_url}...")
    response = httpx.get(schema_url)
    response.raise_for_status()
    spec = response.json()

    # Pre-process: strip internal prefixes from schema names
    spec = strip_prefixes_from_schema(spec)

    # Load aliases as a mapping (Python API expects a dict)
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
        collapse_root_models=True,
    )

    print(f"✅ Models regenerated → {output_file}")


if __name__ == "__main__":
    main()
