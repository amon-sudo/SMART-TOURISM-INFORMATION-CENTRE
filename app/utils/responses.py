from flask import jsonify

class ApiResponse:
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        return jsonify({
            "success": True,
            "data": data,
            "message": message
        }), status_code

    @staticmethod
    def error(message="An error occurred", code="INTERNAL_ERROR", details=None, status_code=500, **kwargs):
        error_payload = {
            "success": False,
            "error": {
                "code": code,
                "message": message
            }
        }
        if details:
            error_payload["error"]["details"] = details
        
        return jsonify(error_payload), status_code
