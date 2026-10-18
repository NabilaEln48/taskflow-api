"""Custom exception handlers.

Why bother? FastAPI's defaults are fine, but two gaps matter in production:

1. Unhandled 500s leak internals. Starlette's default 500 response is
   `"Internal Server Error"` (safe), but we want structured logging AND a
   stable JSON shape clients can rely on.
2. Domain errors deserve domain responses. Instead of raising bare
   HTTPExceptions everywhere, handlers let service code raise meaningful
   exceptions and translate them to HTTP in ONE place.

Registered in main.py via `register_exception_handlers(app)`.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("taskflow")


class TaskFlowError(Exception):
    """Base class for domain errors. Carries an HTTP status + safe message."""

    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail


async def taskflow_error_handler(request: Request, exc: TaskFlowError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


async def unhandled_error_handler(request: Request, exc: Exception):
    # Log the full traceback server-side (we need it to debug)...
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    # ...but send the client a generic message (they must never see
    # tracebacks, SQL, or file paths — that's an information leak).
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(TaskFlowError, taskflow_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
