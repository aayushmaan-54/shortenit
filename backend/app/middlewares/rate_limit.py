import fnmatch

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter

from app.main import app

EXCLUDE_ROUTES = [
    "/",
    "/health",
]
AUTH_ROUTES = [
    "/auth/*",
]

storage = MemoryStorage()
limiter = FixedWindowRateLimiter(storage)

DEFAULT_LIMIT = parse("100/minute")
AUTH_LIMIT = parse("5/minute")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next) -> Response:
    """
    Rate limit routes based on the request path and client IP address;
    Exclude certain routes from rate limiting;
    apply different limits for authentication routes;
    """
    path = request.url.path

    for pattern in EXCLUDE_ROUTES:
        if fnmatch.fnmatch(path, pattern):
            return await call_next(request)

    active_limit = DEFAULT_LIMIT
    for pattern in AUTH_ROUTES:
        if fnmatch.fnmatch(path, pattern):
            active_limit = AUTH_LIMIT
            break  # Stop at the first match

    # Get client IP for the bucket key
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Check if the IP has exceeded the active limit
    if not limiter.hit(active_limit, client_ip):
        return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})

    return await call_next(request)
