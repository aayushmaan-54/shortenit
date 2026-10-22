import fnmatch
import json
import math
import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from limits import RateLimitItem, parse
from limits.aio.storage import RedisStorage
from limits.aio.strategies import MovingWindowRateLimiter
from limits.errors import StorageError

from app.core import logger
from app.core.config import settings
from app.utilities.get_client_ip import get_client_ip

EXCLUDE_ROUTES = [
    "/",
    "/health/*",
]

AUTH_RATE_LIMITS = {
    "*/auth/login": {
        "ip": "20/minute",
        "email": "5/minute",
    },
    "*/auth/register": {
        "ip": "5/hour",
        "email": "3/hour",
    },
    "*/auth/forgot-password": {
        "ip": "5/hour",
        "email": "3/hour",
    },
    "*/auth/reset-password": {
        "ip": "10/hour",
    },
    "*/auth/confirm-user": {
        "ip": "20/hour",
        "email": "5/15minutes",
    },
    "*/auth/resend-confirmation": {
        "ip": "5/hour",
        "email": "3/hour",
    },
    "*/auth/refresh": {
        "ip": "30/minute",
    },
}

# Authenticated requests use `user_id`; anonymous ones fall back to `ip`
DEFAULT_RATE_LIMIT = {
    "user_id": "300/minute",
    "ip": "100/minute",
}
DEFAULT_PATTERN = "default"

MAX_EMAIL_LENGTH = 254

PARSED_AUTH_RATE_LIMITS: dict[str, dict[str, RateLimitItem]] = {
    pattern: {key_type: parse(limit) for key_type, limit in rule.items()}
    for pattern, rule in AUTH_RATE_LIMITS.items()
}
PARSED_DEFAULT_RATE_LIMIT: dict[str, RateLimitItem] = {
    key_type: parse(limit) for key_type, limit in DEFAULT_RATE_LIMIT.items()
}

storage = RedisStorage(
    uri=f"async+{settings.redis_url}",
    key_prefix="rl",
    implementation="redispy",
    wrap_exceptions=True,
)
limiter = MovingWindowRateLimiter(storage)


def _match_rule(path: str, method: str) -> tuple[str, dict[str, RateLimitItem]]:
    """
    Return the (pattern, rule) for the path;
    auth rules apply only to POST so preflight/GET don't consume them
    """
    if method == "POST":
        for pattern, rule in PARSED_AUTH_RATE_LIMITS.items():
            if fnmatch.fnmatch(path, pattern):
                return pattern, rule

    return DEFAULT_PATTERN, PARSED_DEFAULT_RATE_LIMIT


async def _get_email(request: Request) -> str | None:
    """
    Read and normalize `email` from a JSON body;
    return None on any non-JSON/invalid body so only the IP limit applies
    """
    if not request.headers.get("content-type", "").startswith("application/json"):
        return None

    try:
        data = json.loads(await request.body())
    except ValueError:
        return None

    if not isinstance(data, dict):
        return None

    email = data.get("email")
    if not isinstance(email, str):
        return None

    email = email.strip().lower()
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return None

    return email


def _get_user_id(request: Request) -> str | None:
    """Read the user id set by the auth middleware after verifying the token"""
    user_id = getattr(request.state, "user_id", None)
    return str(user_id) if user_id is not None else None


def _select_checks(
    pattern: str,
    rule: dict[str, RateLimitItem],
    identifiers: dict[str, str | None],
) -> list[tuple[str, RateLimitItem, str]]:
    """
    Return the (key_type, limit, value) checks to run;
    default rule: `user_id` if authenticated, else `ip` (exactly one check);
    auth rules: every key that has a value (IP is always present)
    """
    if pattern == DEFAULT_PATTERN:
        user_id = identifiers.get("user_id")
        if user_id is not None:
            return [("user_id", rule["user_id"], user_id)]
        return [("ip", rule["ip"], identifiers["ip"] or "unknown")]

    return [
        (key_type, limit, value)
        for key_type, limit in rule.items()
        if (value := identifiers.get(key_type)) is not None
    ]


def _too_many_requests(reset_time: float) -> JSONResponse:
    """Build the 429 response with a Retry-After header"""
    retry_after = max(1, math.ceil(reset_time - time.time()))
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded"},
        headers={"Retry-After": str(retry_after)},
    )


async def rate_limit_middleware(request: Request, call_next) -> Response:
    """
    Rate limit routes based on the request path, user id, client IP and email;
    Exclude certain routes from rate limiting;
    apply per-route limits for authentication routes;
    other routes: per user when authenticated, per IP otherwise;
    fail open if Redis is unavailable
    """
    path = request.url.path

    # RL Excluded routes
    for pattern in EXCLUDE_ROUTES:
        if fnmatch.fnmatch(path, pattern):
            return await call_next(request)

    pattern, rule = _match_rule(path, request.method)

    identifiers: dict[str, str | None] = {
        "ip": get_client_ip(request),
        "user_id": _get_user_id(request),
    }
    if "email" in rule:
        identifiers["email"] = await _get_email(request)

    try:
        for key_type, limit, value in _select_checks(pattern, rule, identifiers):
            if not await limiter.hit(limit, pattern, key_type, value):
                reset_time, _ = await limiter.get_window_stats(
                    limit, pattern, key_type, value
                )
                return _too_many_requests(reset_time)
    except StorageError:
        logger.exception("Rate limiter storage unavailable; allowing request")

    return await call_next(request)
