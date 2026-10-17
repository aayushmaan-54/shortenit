from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

from app.core import settings

cors_middleware = Middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
