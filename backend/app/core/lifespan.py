from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients import close_redis, ping_redis
from app.repositories.base import BaseRepository

from .config import settings
from .logger import logger


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan event handler;
    start resources before `yield`, stop them after in reverse order
    """
    mode = "development" if settings.debug else "production"
    logger.info("Starting %s in %s mode...", settings.app_name, mode)

    await BaseRepository.ping()
    await ping_redis()
    logger.info("Connected to MongoDB and Redis")

    BaseRepository.create_all_indexes()
    logger.info("MongoDB indexes ensured")

    yield

    await BaseRepository.shutdown()
    await close_redis()
    logger.info("Shutting down %s gracefully...", settings.app_name)
