from redis.asyncio import Redis

from app.core import settings

# Shared async client; connects lazily on first command, closed in app lifespan
redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def ping_redis() -> None:
    """Check Redis is reachable; raises if not so startup fails fast"""
    await redis_client.ping()


async def close_redis() -> None:
    """Close the shared Redis client's connections"""
    await redis_client.aclose()
