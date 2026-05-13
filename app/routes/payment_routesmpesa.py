from flask import Blueprint, request
from app.services.payment_servicesmpesa import process_payment, check_status, handle_callback

payment_mpesa_bp = Blueprint("payment_mpesa_bp", __name__)

# Helper functions for envelopes
def success_response(data, status_code=200):
    return {"success": True, "data": data}, status_code

def error_response(message, code=400):
    return {"success": False, "error": {"code": code, "message": message}}, code

@payment_mpesa_bp.route("/pay/mpesa", methods=["POST"])
def pay_mpesa():
    try:
        data = request.json
        result = process_payment(data)
        return success_response(result)
    except Exception as e:
        return error_response(str(e), 400)

@payment_mpesa_bp.route("/status/<reference>", methods=["GET"])
def status(reference):
    try:
        result = check_status(reference)
        return success_response(result)
    except Exception as e:
        return error_response(str(e), 400)

@payment_mpesa_bp.route("/callback/mpesa", methods=["POST"])
def mpesa_callback():
    try:
        callback_data = request.json
        result = handle_callback(callback_data)
        return success_response(result)
    except Exception as e:
        return error_response(str(e), 400)
