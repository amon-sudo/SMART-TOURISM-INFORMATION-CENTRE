from __future__ import annotations

import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Any

from flask import Flask, jsonify, request
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


# ---------------------------------------------------------------------------
# Structured application error
# ---------------------------------------------------------------------------

class AppError(Exception):
    """
    Raise this anywhere in the Business module to produce a structured
    JSON error response that matches the standard error template:

        {
            "success": false,
            "error": {
                "code": "...",
                "message": "...",
                "trace_id": "...",
                "details": { "timestamp": "..." }
            }
        }
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "APPLICATION_ERROR",
        status_code: int = HTTPStatus.BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = int(status_code)
        self.details = details or {}


# ---------------------------------------------------------------------------
# Common sub-classes used across the Business module
# ---------------------------------------------------------------------------

class NotFoundError(AppError):
    def __init__(self, message: str, *, code: str = "NOT_FOUND", details: dict | None = None):
        super().__init__(message, code=code, status_code=HTTPStatus.NOT_FOUND, details=details)


class ConflictError(AppError):
    def __init__(self, message: str, *, code: str = "CONFLICT", details: dict | None = None):
        super().__init__(message, code=code, status_code=HTTPStatus.CONFLICT, details=details)


class ForbiddenError(AppError):
    def __init__(self, message: str, *, code: str = "FORBIDDEN", details: dict | None = None):
        super().__init__(message, code=code, status_code=HTTPStatus.FORBIDDEN, details=details)


class ValidationAppError(AppError):
    def __init__(self, message: str, *, fields: dict | None = None):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details={"fields": fields or {}},
        )


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _get_trace_id() -> str:
    incoming = request.headers.get("X-Trace-Id", "").strip()
    return incoming if incoming else str(uuid.uuid4())


def _http_status_to_code(status_code: int) -> str:
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        phrase = "Internal Server Error"
    return phrase.upper().replace(" ", "_").replace("-", "_")


def error_response(
    message: str,
    *,
    status_code: int,
    code: str | None = None,
    details: dict[str, Any] | None = None,
):
    """
    Return a Flask (response, status_code) tuple in the standard error shape.

    Usage:
        return error_response("Not found.", status_code=404, code="NOT_FOUND")
    """
    payload_details = {"timestamp": _now_iso(), **(details or {})}
    body = {
        "success": False,
        "error": {
            "code": code or _http_status_to_code(status_code),
            "message": message,
            "trace_id": _get_trace_id(),
            "details": payload_details,
        },
    }
    return jsonify(body), int(status_code)


# ---------------------------------------------------------------------------
# Flask error handler registration
# Attach these to the app in create_app() via register_business_error_handlers(app)
# ---------------------------------------------------------------------------

def register_business_error_handlers(app: Flask) -> None:
    """Register structured error handlers for the Business module on *app*."""

    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        return error_response(
            str(exc),
            status_code=exc.status_code,
            code=exc.code,
            details=exc.details,
        )

    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation(exc: ValidationError):
        return error_response(
            "Validation failed.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            details={"fields": exc.messages},
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return error_response(
            exc.description or "Request failed.",
            status_code=exc.code or 500,
            code=_http_status_to_code(exc.code or 500),
        )

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        app.logger.exception("Unhandled exception: %s", exc)
        return error_response(
            "An unexpected error occurred.",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
        )
