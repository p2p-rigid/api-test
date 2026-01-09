from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """Enumeration of standard error codes."""
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppBaseException(Exception):
    """Base application exception with standardized error code."""
    def __init__(self, error_code: ErrorCode, message: str,
                 field: Optional[str] = None, value: Optional[str] = None, details: Optional[dict] = None):
        self.error_code = error_code
        self.message = message
        self.field = field
        self.value = value
        self.details = details
        super().__init__(message)


class UserNotFoundException(AppBaseException):
    """Raised when a user is not found"""
    def __init__(self, identifier: str):
        super().__init__(
            error_code=ErrorCode.USER_NOT_FOUND,
            message=f"User not found: {identifier}",
            details={"identifier": identifier}
        )


class UserAlreadyExistsException(AppBaseException):
    """Raised when trying to create a user that already exists"""
    def __init__(self, field: str, value: str):
        super().__init__(
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            message=f"User with {field}='{value}' already exists",
            field=field,
            value=value
        )
