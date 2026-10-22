import fnmatch

from fastapi import Request

PUBLIC_ROUTES = [
    "/",
    "/health/*",
    "/auth/login",
    "/auth/register",
    "/auth/forgot-password",
    "/auth/reset-password",
    "/auth/confirm-user",
    "/auth/resend-confirmation",
    "/auth/refresh",
    "/swagger",
    "/docs",
    "/docs/*",
    "/api-docs/*",
]


async def auth_middleware(request: Request, call_next):
    """
    Authenticate the request and check if the path is public or requires authentication;
    """
    path = request.url.path

    for pattern in PUBLIC_ROUTES:
        if fnmatch.fnmatch(path, pattern):
            return await call_next(request)

    # TODO: Handle rest logic
    # add userId in request.state.user_id

    return await call_next(request)
