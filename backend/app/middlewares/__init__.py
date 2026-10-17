from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from .auth import auth_middleware
from .cors import cors_middleware
from .gzip import gzip_middleware
from .https_redirect import https_redirect_middleware
from .logging import logging_middleware
from .rate_limit import rate_limit_middleware
from .request_id import request_id_middleware
from .secure_headers import secure_headers_middleware
from .trusted_host import trusted_host_middleware

app_middlewares = [
    cors_middleware,
    trusted_host_middleware,
    gzip_middleware,
    Middleware(BaseHTTPMiddleware, dispatch=logging_middleware),
    Middleware(BaseHTTPMiddleware, dispatch=request_id_middleware),
    Middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware),
    https_redirect_middleware,
    Middleware(BaseHTTPMiddleware, dispatch=auth_middleware),
    Middleware(BaseHTTPMiddleware, dispatch=secure_headers_middleware),
]
