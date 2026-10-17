from contextlib import asynccontextmanager

from app.core import logger, settings
from app.middlewares import app_middlewares
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler
    """
    mode = "development" if settings.debug else "production"
    logger.info("Starting %s in %s mode...", settings.app_name, mode)
    yield
    logger.info("Shutting down %s gracefully...", settings.app_name)


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


@app.get("/ping", tags=["system"])
async def ping():
    """Endpoint to verify the API is up and running."""
    return {"status": "healthy", "version": app.version}
