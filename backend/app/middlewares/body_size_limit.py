from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.config import settings


async def body_size_limit_middleware(request: Request, call_next) -> Response:
    """
    Reject requests whose body exceeds `settings.max_body_size`;
    based on Content-Length, so it runs before anything reads the body;
    chunked bodies without Content-Length should be capped at the proxy
    """
    content_length = request.headers.get("content-length")

    if content_length is not None:
        try:
            size = int(content_length)
        except ValueError:
            return JSONResponse(
                status_code=400, content={"error": "Invalid Content-Length header"}
            )

        if size > settings.max_body_size:
            return JSONResponse(
                status_code=413, content={"error": "Request body too large"}
            )

    return await call_next(request)
