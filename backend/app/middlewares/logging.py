import time

from fastapi import Request

from app.core import logger
from app.main import app

from .request_id import request_id_context


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Log each request with its method, path, status code, and processing time.
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time

    logger.info(
        "%s %s - %s",
        request.method,
        request.url.path,
        response.status_code,
        extra={
            "request_id": request_id_context.get(),
            "process_time_s": round(process_time, 4),
        },
    )

    return response
