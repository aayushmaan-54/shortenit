from fastapi import FastAPI

from app.api.health import router as health_router
from app.core import settings
from app.core.exception_handlers import exception_handlers
from app.core.lifespan import lifespan
from app.middlewares import app_middlewares

app = FastAPI(
    title=f"{settings.app_name} API",
    debug=settings.debug,
    description=f"`{settings.app_name}` API documentation",
    version="1.0.0",
    contact={
        "name": "Aayushmaan Soni",
        "url": "https://aayushmaansoni.com",
        "email": "hello@aayushmaansoni.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    middleware=app_middlewares,
    exception_handlers=exception_handlers,
    docs_url="/swagger" if settings.debug else None,
    redoc_url="/docs" if settings.debug else None,
    openapi_url=("/api-docs/openapi.json" if settings.debug else None),
)


@app.get("/", summary="API Root & Discovery")
async def root():
    """Root endpoint; Provides basic info"""
    return {
        "app": settings.app_name,
        "version": app.version,
        "environment": "development" if settings.debug else "production",
        "docs_url": "/swagger" if settings.debug else None,
        "redoc_url": "/docs",
        "openapi_url": "/api-docs/openapi.json",
    }


app.include_router(health_router)
