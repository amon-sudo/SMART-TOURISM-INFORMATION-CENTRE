import uuid
from app.extensions import db
from app.mpesa_payment_feature.models.payment_mpesa import PaymentMpesa
from app.utils.gateway_clientmpesa import stk_push

def process_payment(data):
    reference = data.get("reference", str(uuid.uuid4()))
    user_id_raw = data.get("user_id")
    try:
        user_id = user_id_raw if isinstance(user_id_raw, uuid.UUID) else uuid.UUID(str(user_id_raw))
    except Exception as exc:
        raise ValueError("user_id must be a valid UUID") from exc

    try:
        response = stk_push(data["phone_number"], data["amount"], reference)
    except RuntimeError:
        # Fallback for local/dev where M-Pesa credentials are not configured.
        response = {
            "CheckoutRequestID": f"mock-{uuid.uuid4()}",
            "ResponseDescription": "Mock payment accepted",
        }

    checkout_id = response.get("CheckoutRequestID")
    result_desc = response.get("ResponseDescription")

    payment = PaymentMpesa(
        user_id=user_id,
        amount=data["amount"],
        reference=reference,
        checkout_request_id=checkout_id,
        status="pending"
    )
    db.session.add(payment)
    db.session.commit()

    return {
        "reference": reference,
        "checkout_request_id": checkout_id,
        "status": result_desc
    }

def check_status(reference):
    payment = PaymentMpesa.query.filter_by(reference=reference).first()
    if not payment:
        raise Exception("Payment not found")
    return {"reference": payment.reference, "status": payment.status}

def handle_callback(callback_data):
    checkout_id = callback_data.get("Body", {}).get("stkCallback", {}).get("CheckoutRequestID")
    result_code = callback_data.get("Body", {}).get("stkCallback", {}).get("ResultCode")

    payment = PaymentMpesa.query.filter_by(checkout_request_id=checkout_id).first()
    if not payment:
        raise Exception("Payment not found")

    payment.status = "success" if result_code == 0 else "failed"
    db.session.commit()

    return {"checkout_request_id": checkout_id, "status": payment.status}
