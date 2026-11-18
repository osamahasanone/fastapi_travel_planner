"""Our own errors, and the handlers that turn every error into one JSON format.

Every error body: {"error": {"code": "...", "message": "...", "details": [...]}}
("details" only on 422).
"""

from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas import ErrorResponse


# --- the errors our code raises: no HTTP here ----------------------------------
class AppError(Exception):
    """Base class for every error we raise on purpose.

    Subclasses only set two class attributes: a stable code and a default message.
    They know nothing about HTTP: STATUS_CODES below decides each error's status.
    """

    code: str = "bad_request"
    message: str = "Bad request"

    def __init__(
        self, message: str | None = None, details: list[dict[str, Any]] | None = None
    ) -> None:
        self.message = message or self.message
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppError):
    code = "not_found"
    message = "Not found"


class TripNotFound(NotFoundError):
    code = "trip_not_found"
    message = "Trip not found"


class DestinationNotFound(NotFoundError):
    code = "destination_not_found"
    message = "Destination not found"


class DocumentNotFound(NotFoundError):
    code = "document_not_found"
    message = "Document not found"


class UnknownDestination(AppError):
    """The body is valid JSON, but destination_id points to
    nothing: same shape as any 422."""

    code = "validation_error"
    message = "Invalid request"

    def __init__(self, destination_id: int) -> None:
        super().__init__(
            details=[
                {
                    "loc": ["body", "destination_id"],
                    "msg": f"Destination {destination_id} not found",
                    "type": "destination_not_found",
                }
            ]
        )


class FileTooLarge(AppError):
    code = "file_too_large"
    message = "File too large"


class UnsupportedFileType(AppError):
    code = "unsupported_file_type"
    message = "Only PDF, PNG or JPEG files"


# --- the only place that maps our errors to HTTP statuses ----------------------
STATUS_CODES: dict[type, int] = {
    NotFoundError: 404,  # also TripNotFound, DestinationNotFound, DocumentNotFound
    UnknownDestination: 422,
    FileTooLarge: 413,
    UnsupportedFileType: 415,
}


def status_for(exc: AppError) -> int:
    """The status of the closest class in STATUS_CODES:
    TripNotFound -> NotFoundError -> 404."""
    for cls in type(exc).__mro__:  # the class, then its parents
        if cls in STATUS_CODES:
            return STATUS_CODES[cls]
    return 400


# --- one place that builds every error body -----------------------------------
def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse({"error": error}, status_code=status_code, headers=headers)


def status_code_name(status_code: int) -> str:
    """404 -> "not_found", 405 -> "method_not_allowed"."""
    return HTTPStatus(status_code).phrase.lower().replace(" ", "_").replace("-", "_")


# --- the handlers ---------------------------------------------------------------
async def app_error_handler(request: Request, exc: AppError) -> Response:
    return error_response(status_for(exc), exc.code, exc.message, exc.details)


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> Response:
    """HTTPException from FastAPI, Starlette's routing (404, 405) or a library."""
    if exc.status_code in (204, 304):  # these statuses can't have a body
        return Response(status_code=exc.status_code, headers=exc.headers)
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return error_response(
        exc.status_code,
        status_code_name(exc.status_code),
        message,
        headers=exc.headers,  # keeps e.g. "Allow: GET" on a 405
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    details = [
        {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
        for e in exc.errors()
    ]
    return error_response(422, "validation_error", "Invalid request", details)


async def unhandled_error_handler(request: Request, exc: Exception) -> Response:
    """A bug. The client gets no details; the traceback still goes to the server log."""
    return error_response(500, "internal_error", "Internal server error")


def error_docs(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """For responses=: error_docs(404, 422) documents both
    with the ErrorResponse body."""
    return {
        code: {"model": ErrorResponse, "description": HTTPStatus(code).phrase}
        for code in status_codes
    }


def add_error_handlers(app: FastAPI) -> None:
    """Register every handler. Same as decorating each one
    with @app.exception_handler(...)."""
    app.exception_handler(AppError)(app_error_handler)
    app.exception_handler(StarletteHTTPException)(http_error_handler)
    app.exception_handler(RequestValidationError)(validation_error_handler)
    app.exception_handler(Exception)(unhandled_error_handler)
