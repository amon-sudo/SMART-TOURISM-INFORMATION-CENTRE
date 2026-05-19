from __future__ import annotations

from flask import jsonify


class ApiResponse:
    @staticmethod
    def success(data=None, message: str = "Success", status_code: int = 200):
        payload = {
            "success": True,
            "message": message,
            "data": data,
        }
        return jsonify(payload), status_code

    @staticmethod
    def error(
        message: str,
        status_code: int = 400,
        code: str | None = None,
        details=None,
    ):
        payload = {
            "success": False,
            "message": message,
        }
        if code is not None:
            payload["code"] = code
        if details is not None:
            payload["details"] = details
        return jsonify(payload), status_code
