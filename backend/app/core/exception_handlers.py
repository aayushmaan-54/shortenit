from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Starlette's, not FastAPI's: routing errors (404/405) raise Starlette's base class,
# which a handler for FastAPI's subclass misses; this one catches both
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utilities import add_secure_headers

from .config import settings
from .exceptions import AppException

# First `loc` item is where the value came from (body/query/path/...), not part of the field
LOC_SOURCE_INDEX = 1


def build_error_response(
    request: Request,
    status_code: int,
    error_code: str,
    message: str,
    details: Any = None,
    headers: Mapping[str, str] | None = None,
):
    """Builds a standardized error response"""
    req_id = getattr(request.state, "request_id", "unknown")

    content = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
        },
        "request_id": req_id,
    }

    if details is not None:
        content["error"]["details"] = details

    response = JSONResponse(
        status_code=status_code,
        content=content,
        headers={**(headers or {}), "X-Request-ID": req_id},
    )

    # Unhandled errors may bypass CORS middleware, causing browsers to block the frontend
    # Add CORS headers manually for allowed origins to ensure the frontend can read the error response
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"

    add_secure_headers(request.url.path, response)
    return response


async def app_exception_handler(request: Request, exc: AppException):
    """Custom application errors"""
    return build_error_response(
        request=request,
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Framework-raised errors"""
    try:
        error_code = HTTPStatus(exc.status_code).name
    except ValueError:
        # Non-standard codes (e.g. 499) have no name
        error_code = "HTTP_ERROR"

    return build_error_response(
        request=request,
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail),
        headers=exc.headers,
    )


def _format_validation_error(error: dict[str, Any]) -> dict[str, Any]:
    """
    Shape one pydantic error for the frontend
    """
    # Malformed JSON reports a character position, not a field
    path = [] if error["type"] == "json_invalid" else error["loc"][LOC_SOURCE_INDEX:]

    return {
        "field": ".".join(str(part) for part in path) or None,
        "message": error["msg"],
        "type": error["type"],
    }


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic validation errors"""
    return build_error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details=[_format_validation_error(error) for error in exc.errors()],
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Unhandeled Error"""
    message = (
        str(exc) if settings.debug else "Internal server error. Please try again later."
    )

    return build_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        message=message,
    )


# Mapping dictionary for FastAPI(exception_handlers=...)
exception_handlers = {
    AppException: app_exception_handler,
    StarletteHTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    Exception: unhandled_exception_handler,
}
