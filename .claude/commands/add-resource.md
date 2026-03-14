Add a new API resource to the SDK. The user will specify the resource name and endpoints.

1. Create a new resource file in src/amigo_sdk/resources/{resource_name}.py following the pattern of existing resources (both async and sync classes)
2. Export it from src/amigo_sdk/resources/__init__.py
3. Add the resource as properties on both AsyncAmigoClient and AmigoClient in src/amigo_sdk/sdk_client.py
4. Add tests in tests/resources/test_{resource_name}.py using the test helpers from tests/resources/helpers.py
5. Run tests to verify
