from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware import Middleware

# min 1000 bytes for gzip compression to be applied
gzip_middleware = Middleware(GZipMiddleware, minimum_size=1000)
