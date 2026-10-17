from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware import Middleware

gzip_middleware = Middleware(GZipMiddleware, minimum_size=1000)
