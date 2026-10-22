import time

from fastapi import Request

from app.core import logger

from .request_id import request_id_context


async def logging_middleware(request: Request, call_next):
    """
    Log each request with its method, path, status code, and processing time.
    """
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        # Unhandled errors never produce a response here; log them as 500 and re-raise
        logger.exception(
            "%s %s - 500",
            request.method,
            request.url.path,
            extra={
                "request_id": request_id_context.get(),
                "process_time_s": round(time.perf_counter() - start_time, 4),
            },
        )
        raise
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
