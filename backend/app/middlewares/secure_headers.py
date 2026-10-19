from fastapi import Request, Response

from app.main import app


@app.middleware("http")
async def secure_headers_middleware(request: Request, call_next) -> Response:
    """
    Middleware to add secure headers to the response;
    Protect against common web vulnerabilities;
    """
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Clickjacking protection
    response.headers["X-Frame-Options"] = "DENY"

    # Block reflected XSS attacks for older browsers
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Enforce HTTPS for one year and include subdomains
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

    # Restrict content sources to the same origin
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    # Only pass domain in referrer header for same-origin requests, and only send the origin for cross-origin requests
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Remove server header to obscure FastAPI tech stack
    if "server" in response.headers:
        del response.headers["server"]

    return response
