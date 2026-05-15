from __future__ import annotations

import uuid
from datetime import datetime
from http import HTTPStatus
from typing import Any

from flask import Flask, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers for the Flask application."""

    def format_error_response(code: str, message: str, details: list[dict[str, str]] = None) -> dict:
        """Format error responses in the envelope format."""
        return {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "details": details or []
            }
        }

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException) -> Any:
        """Handle HTTP exceptions and return JSON responses."""
        return jsonify(format_error_response(
            code=e.name.replace(" ", "_"),
            message=e.description,
        )), e.code

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError) -> Any:
        """Handle Marshmallow validation errors."""
        return jsonify(format_error_response(
            code="VALIDATION_FAILED",
            message="The request payload failed schema validation.",
            details=[{"field": field, "issue": issue} for field, issues in e.messages.items() for issue in issues]
        )), HTTPStatus.BAD_REQUEST

    @app.errorhandler(Exception)
    def handle_generic_exception(e: Exception) -> Any:
        """Handle any uncaught exceptions."""
        error_id = str(uuid.uuid4())
        app.logger.error(f"Unhandled exception (ID: {error_id}): {e}")
        return jsonify(format_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please contact support with the error ID.",
            details=[{"error_id": error_id}]
        )), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.errorhandler(HTTPStatus.NOT_FOUND)
    def handle_not_found(e: HTTPException) -> Any:
        """Handle 404 Not Found errors."""
        return jsonify(format_error_response(
            code="NOT_FOUND",
            message="The requested resource was not found."
        )), HTTPStatus.NOT_FOUND

class CustomError(Exception):
    """Base class for custom exceptions in the transport feature."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class ResourceNotFoundError(CustomError):
    """Exception raised when a requested resource is not found."""
    pass

