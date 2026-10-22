from redis.asyncio import Redis

from app.core.config import settings

# Shared async client; connects lazily on first command, closed in app lifespan
redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    """Close the shared Redis client's connections"""
    await redis_client.aclose()
