import uuid
from contextvars import ContextVar

from app.main import app
from fastapi import Request

request_id_context: ContextVar[str] = ContextVar("request_id", default="unknown")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """
    Generate unique req id for each req;
    add that to res header;
    store in contextvar for logging
    """
    request_id = str(uuid.uuid4())
    token = request_id_context.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    request_id_context.reset(token)
    return response
