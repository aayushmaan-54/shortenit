from typing import Any


class AppException(Exception):
    """Base class for all application errors"""

    def __init__(
        self,
        message: str = "Something went wrong",
        error_code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        self.headers = headers
        super().__init__(message)


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request", details: Any = None):
        super().__init__(
            message=message,
            error_code="BAD_REQUEST",
            status_code=400,
            details=details,
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", details: Any = None):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
            details=details,
            # RFC 9110: a 401 must tell the client which auth scheme to use
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", details: Any = None):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
            details=details,
        )


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Any = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class ConflictException(AppException):
    def __init__(self, message: str = "Resource conflict", details: Any = None):
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=details,
        )


class PayloadTooLargeException(AppException):
    def __init__(self, message: str = "Request body too large", details: Any = None):
        super().__init__(
            message=message,
            error_code="PAYLOAD_TOO_LARGE",
            status_code=413,
            details=details,
        )


class TooManyRequestsException(AppException):
    def __init__(
        self,
        retry_after: int,
        message: str = "Rate limit exceeded",
        details: Any = None,
    ):
        super().__init__(
            message=message,
            error_code="TOO_MANY_REQUESTS",
            status_code=429,
            details=details,
            headers={"Retry-After": str(retry_after)},
        )
