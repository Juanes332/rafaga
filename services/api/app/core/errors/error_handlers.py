"""Translate exceptions into the one error contract, inside the factory."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors.error_contract import AppError, ErrorBody

logger = logging.getLogger(__name__)


async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Answer a deliberate domain failure with its own status."""
    return JSONResponse(
        status_code=exc.status_code, content=exc.as_body(), headers=exc.headers
    )


async def _validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Answer a malformed request with 422, listing only locations."""
    fields = [
        {"loc": [str(p) for p in e.get("loc", ())], "type": e.get("type", "")}
        for e in exc.errors()
    ]
    body = ErrorBody(
        code="validation_error",
        message="The request payload is invalid.",
        details={"errors": fields},
    )
    return JSONResponse(
        status_code=422,
        content=body.model_dump(exclude_none=True),
    )


async def _http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Reshape framework-raised HTTPExceptions into the contract."""
    body = ErrorBody(code="http_error", message=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(exclude_none=True),
        headers=getattr(exc, "headers", None),
    )


async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    """Answer an unforeseen failure with 500 and leak nothing."""
    logger.exception("unhandled_error path=%s", request.url.path)
    body = ErrorBody(
        code="internal_error", message="The request could not be completed."
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=body.model_dump(exclude_none=True),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach every handler to the app, called from create_app()."""
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
