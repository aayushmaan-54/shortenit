from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware import Middleware

from app.core.config import settings

trusted_host_middleware = Middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)
