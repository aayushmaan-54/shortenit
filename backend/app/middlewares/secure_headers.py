import fnmatch

from fastapi import Request, Response

# Swagger/ReDoc load JS/CSS from a CDN; the strict API CSP would break them
DOCS_ROUTES = [
    "/swagger",
    "/docs",
    "/docs/*",
    "/api-docs/*",
]

# Responses carrying tokens/credentials must not be cached
NO_STORE_ROUTES = [
    "/auth/*",
]


def add_secure_headers(path: str, response: Response) -> Response:
    """
    Add secure headers to the response;
    Protect against common web vulnerabilities;
    `server` header is removed via uvicorn `--no-server-header` (added after middleware runs)
    """
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Clickjacking protection
    response.headers["X-Frame-Options"] = "DENY"

    # Disable the legacy XSS auditor; it is deprecated and can introduce vulnerabilities
    response.headers["X-XSS-Protection"] = "0"

    # Enforce HTTPS for one year and include subdomains
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

    # JSON API serves no content; block everything and disallow framing
    if not any(fnmatch.fnmatch(path, pattern) for pattern in DOCS_ROUTES):
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )

    # Only pass domain in referrer header for same-origin requests, and only send the origin for cross-origin requests
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Don't let browsers/proxies cache auth responses (tokens)
    if any(fnmatch.fnmatch(path, pattern) for pattern in NO_STORE_ROUTES):
        response.headers["Cache-Control"] = "no-store"

    return response


async def secure_headers_middleware(request: Request, call_next) -> Response:
    """
    Middleware to add secure headers to every response
    """
    response = await call_next(request)
    return add_secure_headers(request.url.path, response)
