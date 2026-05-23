import uuid
import os
from app.extensions import db
from app.mpesa_payment_feature.models.payment_mpesa import PaymentMpesa
from app.utils.gateway_clientmpesa import stk_push


def _confirm_booking(booking_id):
    """Confirm a booking after successful payment."""
    try:
        from app.models.booking import Booking, BookingStatus
        booking = Booking.query.get(booking_id)
        if booking and booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CONFIRMED
            db.session.commit()
    except Exception:
        db.session.rollback()


def process_payment(data):
    reference = data.get("reference", str(uuid.uuid4()))
    user_id_raw = data.get("user_id")
    booking_id_raw = data.get("booking_id")
    try:
        user_id = user_id_raw if isinstance(user_id_raw, uuid.UUID) else uuid.UUID(str(user_id_raw))
    except Exception as exc:
        raise ValueError("user_id must be a valid UUID") from exc

    booking_id = None
    if booking_id_raw:
        try:
            booking_id = booking_id_raw if isinstance(booking_id_raw, uuid.UUID) else uuid.UUID(str(booking_id_raw))
        except Exception:
            pass

    is_mock = False
    try:
        response = stk_push(data["phone_number"], data["amount"], reference)
    except RuntimeError:
        # Fallback for local/dev where M-Pesa credentials are not configured.
        is_mock = True
        response = {
            "CheckoutRequestID": f"mock-{uuid.uuid4()}",
            "ResponseDescription": "Mock payment accepted",
        }

    checkout_id = response.get("CheckoutRequestID")
    result_desc = response.get("ResponseDescription")

    # In dev mock mode, immediately mark payment as success.
    initial_status = "success" if is_mock else "pending"

    payment = PaymentMpesa(
        user_id=user_id,
        booking_id=booking_id,
        amount=data["amount"],
        reference=reference,
        checkout_request_id=checkout_id,
        status=initial_status,
    )
    db.session.add(payment)
    db.session.commit()

    # Auto-confirm booking in dev mock mode.
    if is_mock and booking_id:
        _confirm_booking(booking_id)

    return {
        "reference": reference,
        "checkout_request_id": checkout_id,
        "status": result_desc,
        "mock": is_mock,
    }

def check_status(reference):
    payment = PaymentMpesa.query.filter_by(reference=reference).first()
    if not payment:
        raise Exception("Payment not found")
    return {
        "reference": payment.reference,
        "status": payment.status,
        "booking_id": str(payment.booking_id) if payment.booking_id else None,
    }

def handle_callback(callback_data):
    checkout_id = callback_data.get("Body", {}).get("stkCallback", {}).get("CheckoutRequestID")
    result_code = callback_data.get("Body", {}).get("stkCallback", {}).get("ResultCode")

    payment = PaymentMpesa.query.filter_by(checkout_request_id=checkout_id).first()
    if not payment:
        raise Exception("Payment not found")

    payment.status = "success" if result_code == 0 else "failed"
    db.session.commit()

    # Auto-confirm linked booking when payment succeeds.
    if payment.status == "success" and payment.booking_id:
        _confirm_booking(payment.booking_id)

    return {"checkout_request_id": checkout_id, "status": payment.status}
