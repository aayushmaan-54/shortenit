from fastapi import Request, Response

from app.core import (
    BadRequestException,
    PayloadTooLargeException,
    app_exception_handler,
    settings,
)


async def body_size_limit_middleware(request: Request, call_next) -> Response:
    """
    Reject requests whose body exceeds `settings.max_body_size`;
    based on Content-Length, so it runs before anything reads the body;
    """
    content_length = request.headers.get("content-length")

    if content_length is not None:
        try:
            size = int(content_length)
        except ValueError:
            return await app_exception_handler(
                request, BadRequestException("Invalid Content-Length header")
            )

        if size > settings.max_body_size:
            return await app_exception_handler(request, PayloadTooLargeException())

    return await call_next(request)
