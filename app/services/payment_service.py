"""
Payment Service — Refund Assessment & Processing
Handles refund workflows for cancelled bookings.
"""

import logging
import uuid
from flask import has_request_context, request
from app.extensions import db
from app.models.booking import Booking, BookingStatus
from app.payment_stripe.models.models import PaymentStripe
from app.audit.services.audit_log_service import create_audit_log

logger = logging.getLogger(__name__)


def _write_audit_log(payload: dict) -> None:
    try:
        create_audit_log(payload)
    except Exception as exc:
        logger.warning("Failed to write payment audit log: %s", exc)


class PaymentService:
    """Service for managing payment operations including refunds."""

    @staticmethod
    def _get_payment_for_booking(booking_id: uuid.UUID) -> PaymentStripe | None:
        # Prefer direct FK if present in the runtime model; otherwise fallback
        # to metadata linkage used by current Stripe payment records.
        if hasattr(PaymentStripe, "booking_id"):
            return PaymentStripe.query.filter_by(booking_id=booking_id).first()

        booking_id_str = str(booking_id)
        for payment in PaymentStripe.query.order_by(PaymentStripe.created_at.desc()).all():
            metadata = payment.payment_metadata or {}
            if str(metadata.get("booking_id")) == booking_id_str:
                return payment
        return None

    @staticmethod
    def initiate_refund_assessment(booking_id: str | uuid.UUID) -> bool:
        """
        Initiate refund assessment for a cancelled confirmed booking.
        
        Args:
            booking_id: UUID of the booking to refund
            
        Returns:
            bool: True if refund was initiated, False if no refund was needed
        """
        try:
            # Normalize booking_id
            if isinstance(booking_id, str):
                booking_id = uuid.UUID(booking_id)
            
            # Find the booking
            booking = Booking.query.filter_by(id=booking_id).first()
            if not booking:
                logger.warning(f"Booking {booking_id} not found for refund assessment")
                return False
            
            # Only refund if booking was confirmed and has a payment
            if booking.status != BookingStatus.CONFIRMED:
                logger.info(f"Booking {booking_id} not in CONFIRMED state, skipping refund")
                return False
            
            # Find associated Stripe payment
            payment = PaymentService._get_payment_for_booking(booking_id)
            if not payment:
                logger.warning(f"No payment found for booking {booking_id}")
                return False
            
            # If payment was already succeeded, initiate refund
            if payment.status == "succeeded" and payment.stripe_payment_intent_id:
                logger.info(
                    f"Marking payment {payment.id} for refund assessment "
                    f"(booking {booking_id})"
                )
                old_status = payment.status
                # Update payment status to indicate refund in progress
                payment.status = "refund_initiated"
                db.session.add(payment)
                db.session.commit()

                _write_audit_log({
                    "actor_user_id": str(booking.user_id) if booking.user_id else None,
                    "action": "payment_refund_initiated",
                    "entity_type": "payment_stripe",
                    "entity_id": str(payment.id),
                    "old_values": {"status": old_status},
                    "new_values": {
                        "status": payment.status,
                        "booking_id": str(booking.id),
                        "stripe_payment_intent_id": payment.stripe_payment_intent_id,
                    },
                    "ip_address": request.remote_addr if has_request_context() else None,
                    "user_agent": request.headers.get("User-Agent") if has_request_context() else None,
                })
                return True
            
            logger.info(f"Payment {payment.id} not eligible for refund (status: {payment.status})")
            return False
            
        except Exception as exc:
            logger.error(f"Error assessing refund for booking {booking_id}: {exc}")
            return False
