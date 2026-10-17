import fnmatch

from app.main import app
from fastapi import Request

PUBLIC_ROUTES = [
    "/",
    "/health",
    "/auth/login",
    "/auth/register",
    "/docs",
    "/openapi.json",
]


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Authenticate the request and check if the path is public or requires authentication;
    """
    path = request.url.path

    for pattern in PUBLIC_ROUTES:
        if fnmatch.fnmatch(path, pattern):
            return await call_next(request)

    # TODO: Handle rest logic

    return await call_next(request)
