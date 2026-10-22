import asyncio
from collections.abc import Awaitable, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.clients.redis import redis_client
from app.core import logger

router = APIRouter(prefix="/health", tags=["system"])

CHECK_TIMEOUT_S = 1.0


async def _check_redis() -> None:
    await redis_client.ping()


# Add new dependencies here (e.g. "db": _check_db)
READINESS_CHECKS: dict[str, Callable[[], Awaitable[None]]] = {
    "redis": _check_redis,
}


async def _run_check(
    name: str, check: Callable[[], Awaitable[None]]
) -> tuple[str, bool]:
    """Run one check with a timeout; never raise, so one failure can't break the others"""
    try:
        await asyncio.wait_for(check(), timeout=CHECK_TIMEOUT_S)
        return name, True
    except Exception:
        logger.warning("Readiness check failed: %s", name, exc_info=True)
        return name, False


@router.get("/live", summary="Liveness probe")
async def live():
    """Process is up; checks no dependencies so a DB/Redis blip doesn't trigger restarts"""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def ready() -> JSONResponse:
    """
    All dependencies reachable;
    returns 503 if any check fails so the load balancer stops routing traffic here;
    error details are logged, not returned
    """
    results = await asyncio.gather(
        *(_run_check(name, check) for name, check in READINESS_CHECKS.items())
    )
    healthy = all(ok for _, ok in results)

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "unavailable",
            "checks": {name: "ok" if ok else "down" for name, ok in results},
        },
    )
