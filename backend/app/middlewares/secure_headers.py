from fastapi import Request, Response

from app.utilities import add_secure_headers


async def secure_headers_middleware(request: Request, call_next) -> Response:
    """
    Middleware to add secure headers to every response
    """
    response = await call_next(request)
    return add_secure_headers(request.url.path, response)
