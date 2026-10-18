import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("taskflow")

class TaskFlowError(Exception):

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

    logger.exception("Unhandled error on %s %s", request.method, request.url.path)

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(TaskFlowError, taskflow_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
