from flask import Blueprint, request
from app.services.payment_servicesmpesa import process_payment, check_status, handle_callback
from app.utils.responses import ApiResponse
import logging

logger = logging.getLogger(__name__)

payment_mpesa_bp = Blueprint("payment_mpesa_bp", __name__)

@payment_mpesa_bp.route("/pay/mpesa", methods=["POST"])
def pay_mpesa():
    try:
        data = request.json or {}
        if not data.get("phone_number") or not data.get("amount") or not data.get("user_id"):
             return ApiResponse.error(message="Missing required fields", code="MISSING_FIELDS", status_code=400)
             
        result = process_payment(data)
        return ApiResponse.success(data=result, message="M-Pesa STK push initiated")
    except Exception as e:
        logger.error(f"M-Pesa pay error: {str(e)}")
        return ApiResponse.error(message=str(e), code="MPESA_PAY_ERROR", status_code=400)

@payment_mpesa_bp.route("/status/<reference>", methods=["GET"])
def status(reference):
    try:
        result = check_status(reference)
        return ApiResponse.success(data=result)
    except Exception as e:
        logger.error(f"M-Pesa status error: {str(e)}")
        return ApiResponse.error(message=str(e), code="MPESA_STATUS_ERROR", status_code=404)

@payment_mpesa_bp.route("/callback/mpesa", methods=["POST"])
def mpesa_callback():
    try:
        callback_data = request.json
        logger.info(f"M-Pesa callback received: {callback_data}")
        result = handle_callback(callback_data)
        return ApiResponse.success(data=result, message="Callback processed")
    except Exception as e:
        logger.error(f"M-Pesa callback error: {str(e)}")
        return ApiResponse.error(message=str(e), code="MPESA_CALLBACK_ERROR", status_code=400)
