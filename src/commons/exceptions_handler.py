import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from commons.log_helper import get_logger

_LOG = get_logger(__name__)


def register_exception_handlers(app: "FastAPI") -> None:
    """Register all global exception handlers."""

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        _LOG.warning(f"ValidationError; Path: {request.url}; Error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Validation error", "errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code >= 500:
            trace = traceback.format_exc()
            _LOG.error(
                f"Unexpected; Path: {request.url}; Error: {exc}; Traceback: {trace}"
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Internal server error"},
            )
        else:
            _LOG.warning(
                f"HTTPError; Path: {request.url}; Status: {exc.status_code}; Detail: {exc.detail}"
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"message": exc.detail},
            )

    @app.exception_handler(Exception)
    async def general_handler(request: Request, exc: Exception):
        trace = traceback.format_exc()
        _LOG.error(f"Unexpected; Path: {request.url}; Error: {exc}; Traceback: {trace}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Internal server error"},
        )
