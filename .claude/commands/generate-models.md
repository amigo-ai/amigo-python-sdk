Regenerate Pydantic models from the OpenAPI spec:
1. Run `python scripts/gen_models.py` to fetch the latest OpenAPI schema and generate models
2. Verify the generated files in src/amigo_sdk/generated/
3. Run `ruff check` on generated files
4. Run `pytest` to ensure nothing is broken
