from fastapi import FastAPI

from app.api import api_router, health_router
from app.core import exception_handlers, settings
from app.core.lifespan import lifespan
from app.middlewares import app_middlewares

app = FastAPI(
    title=f"{settings.app_name} API",
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
        "redoc_url": "/docs" if settings.debug else None,
        "openapi_url": "/api-docs/openapi.json" if settings.debug else None,
    }


app.include_router(health_router)
app.include_router(api_router, prefix="/api")
