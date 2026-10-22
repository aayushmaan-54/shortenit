from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.middlewares.secure_headers import add_secure_headers


async def unhandled_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
    """
    Return a consistent JSON 500 for any unhandled exception;
    runs outside all app middlewares, so CORS and secure headers are added here;
    the traceback is already logged by the logging middleware
    """
    request_id = getattr(request.state, "request_id", "unknown")

    response = JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )

    # Without CORS headers the browser hides the 500 behind a CORS error
    origin = request.headers.get("origin")
    if origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"

    add_secure_headers(request.url.path, response)
    return response


exception_handlers: dict[
    int | type[Exception], Callable[[Request, Any], Coroutine[Any, Any, Response]]
] = {
    Exception: unhandled_exception_handler,
}
