import uuid
from contextvars import ContextVar

from fastapi import Request, Response


request_id_context: ContextVar[str] = ContextVar("request_id", default="unknown")


async def request_id_middleware(request: Request, call_next) -> Response:
    """
    Generate unique req id for each req;
    add that to res header;
    store in contextvar for logging
    """
    request_id = str(uuid.uuid4())
    # Also on request.state: the global exception handler runs after the contextvar is reset
    request.state.request_id = request_id
    token = request_id_context.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        # Reset even if the request raised, so the id never leaks into another request
        request_id_context.reset(token)
