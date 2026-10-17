from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware import Middleware

from backend.app.core.config import settings

https_redirect_middleware = (
    Middleware(HTTPSRedirectMiddleware) if settings.debug is False else None
)
