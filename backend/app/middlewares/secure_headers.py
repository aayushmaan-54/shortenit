from app.main import app
from fastapi import Request


@app.middleware("http")
async def secure_headers_middleware(request: Request, call_next):
    """
    Middleware to add secure headers to the response;
    Protect against common web vulnerabilities;
    """
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Remove server header to obscure FastAPI tech stack
    if "server" in response.headers:
        del response.headers["server"]

    return response
