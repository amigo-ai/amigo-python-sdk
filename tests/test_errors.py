import pytest
from unittest.mock import Mock

from src.errors import (
    AmigoError,
    AuthenticationError,
    BadRequestError,
    ValidationError,
    ServerError,
    get_error_class_for_status_code,
    raise_for_status,
)


@pytest.mark.unit
class TestSDKErrors:
    """Simple test suite for SDK error functionality."""

    def test_status_code_mapping(self):
        """Test that status codes map to correct error types."""
        test_cases = [
            (401, AuthenticationError),
            (400, BadRequestError),
            (422, ValidationError),
            (500, ServerError),
            (418, BadRequestError),  # Unknown 4xx
        ]

        for status_code, expected_class in test_cases:
            error_class = get_error_class_for_status_code(status_code)
            assert error_class == expected_class

    def test_error_inheritance(self):
        """Test that error inheritance works correctly."""
        validation_error = ValidationError("Validation failed")
        assert isinstance(validation_error, ValidationError)
        assert isinstance(validation_error, BadRequestError)
        assert isinstance(validation_error, AmigoError)

    def test_error_with_details(self):
        """Test error initialization with status and error codes."""
        error = AmigoError("Test error", status_code=400, error_code="TEST_CODE")
        assert error.status_code == 400
        assert error.error_code == "TEST_CODE"
        assert "Test error (HTTP 400) [TEST_CODE]" == str(error)

    def test_validation_error_with_field_errors(self):
        """Test ValidationError with field error details."""
        field_errors = {"email": "Invalid format"}
        error = ValidationError("Validation failed", field_errors=field_errors)
        assert error.field_errors == field_errors

    def test_raise_for_status_success(self):
        """Test that raise_for_status does nothing for successful responses."""
        mock_response = Mock()
        mock_response.is_success = True

        # Should not raise
        raise_for_status(mock_response)

    def test_raise_for_status_with_error(self):
        """Test raise_for_status with error response."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid API key"}

        with pytest.raises(AuthenticationError) as exc_info:
            raise_for_status(mock_response)

        error = exc_info.value
        assert error.status_code == 401
        assert "Invalid API key" in str(error)
