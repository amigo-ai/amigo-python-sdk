from pathlib import Path
import httpx
from datamodel_code_generator import InputFileType, generate
from datamodel_code_generator import DataModelType


def main() -> None:
    schema_url = "https://api.amigo.ai/v1/openapi.json"
    out_dir = Path(__file__).parent.parent / "src" / "generated"
    output_file = out_dir / "model.py"

    # Create the generated directory if it doesn't exist
    out_dir.mkdir(parents=True, exist_ok=True)

    # Remove existing model.py if it exists
    if output_file.exists():
        output_file.unlink()

    # Fetch the OpenAPI schema from the remote URL
    print(f"Fetching OpenAPI schema from {schema_url}...")
    response = httpx.get(schema_url)
    response.raise_for_status()
    openapi_content = response.text

    generate(
        openapi_content,
        input_file_type=InputFileType.OpenAPI,
        output=output_file,
        output_model_type=DataModelType.PydanticV2BaseModel,
    )

    print(f"✅ Models regenerated → {output_file}")


if __name__ == "__main__":
    main()
