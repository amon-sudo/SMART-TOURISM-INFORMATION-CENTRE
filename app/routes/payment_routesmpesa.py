from flask import Blueprint, request, jsonify
from app.services.payment_servicesmpesa import process_payment, check_status, handle_callback

payment_mpesa_bp = Blueprint("payment_mpesa_bp", __name__)

@payment_mpesa_bp.route("/pay/mpesa", methods=["POST"])
def pay_mpesa():
    data = request.json
    result = process_payment(data)
    return jsonify(result)

@payment_mpesa_bp.route("/status/<reference>", methods=["GET"])
def status(reference):
    result = check_status(reference)
    return jsonify(result)

@payment_mpesa_bp.route("/callback/mpesa", methods=["POST"])
def mpesa_callback():
    callback_data = request.json
    result = handle_callback(callback_data)
    return jsonify(result)
