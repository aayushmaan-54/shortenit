from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.redis import close_redis
from app.core.config import settings
from app.core.logger import logger


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan event handler;
    start resources before `yield`, stop them after in reverse order
    """
    mode = "development" if settings.debug else "production"
    logger.info("Starting %s in %s mode...", settings.app_name, mode)

    yield

    await close_redis()
    logger.info("Shutting down %s gracefully...", settings.app_name)
