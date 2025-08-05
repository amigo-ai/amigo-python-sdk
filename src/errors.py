from typing import Any, Optional


class AmigoError(Exception):
    """
    Base class for Amigo API errors.
    """
    
    def __init__(self, message: str, *, status_code: Optional[int] = None, error_code: Optional[str] = None, response_body: Optional[Any] = None) -> None:
       super().__init__(message)
       self.status_code = status_code
       self.error_code = error_code
       self.response_body = response_body

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        return " ".join(parts)

# ---- 4xx client errors ------------------------------------------------------
class BadRequestError(AmigoError): # 400
    pass

class AuthenticationError(AmigoError): # 401
    pass

class PermissionError(AmigoError): # 403
    pass

class NotFoundError(AmigoError): # 404
    pass

class ConflictError(AmigoError): # 409
    pass

class RateLimitError(AmigoError): # 429
    pass

# ---- Validation / semantic errors ------------------------------------------
class ValidationError(BadRequestError):  # 422 or 400 with `errors` list
    def __init__(self, *args, field_errors: Optional[dict[str, str]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_errors = field_errors or {}

# ---- 5xx server errors ------------------------------------------------------
class ServerError(AmigoError): # 500
    pass

class ServiceUnavailableError(ServerError): # 503 / maintenance
    pass

# ---- Internal SDK issues ----------------------------------------------------
class SDKInternalError(AmigoError):
    """JSON decoding failure, Pydantic model mismatch, etc."""