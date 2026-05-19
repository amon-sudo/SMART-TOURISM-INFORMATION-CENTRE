import stripe
import os
import logging
import uuid
import json
from types import SimpleNamespace
from decimal import Decimal
from app.extensions import db
from app.payment_stripe.models.models import PaymentStripe, StripeWebhookEvent

# Configure logging
logger = logging.getLogger(__name__)

class StripeService:
    @staticmethod
    def _get_api_key():
        key = os.getenv("STRIPE_SECRET_KEY")
        return key

    @staticmethod
    def create_payment_intent(user_id, amount, currency="usd", metadata=None):
        """
        Creates a Stripe PaymentIntent and records it in the database.
        amount: integer in cents
        """
        # Validate booking_id in metadata
        if not metadata or 'booking_id' not in metadata:
            raise ValueError("Metadata must contain a 'booking_id'")
        
        try:
            uuid.UUID(metadata['booking_id'])
        except ValueError:
            raise ValueError("Invalid 'booking_id' format in metadata")

        try:
            user_id = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        except Exception as exc:
            raise ValueError("Invalid user_id format") from exc

        api_key = StripeService._get_api_key()
        try:
            if api_key:
                stripe.api_key = api_key
                intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency=currency,
                    metadata=metadata,
                    automatic_payment_methods={"enabled": True},
                )
            else:
                # Local smoke-test fallback when Stripe keys are not configured.
                mock_intent_id = f"pi_mock_{uuid.uuid4().hex[:20]}"
                intent = SimpleNamespace(
                    id=mock_intent_id,
                    client_secret=f"{mock_intent_id}_secret_mock",
                )

            payment = PaymentStripe(
                user_id=user_id,
                amount=Decimal(amount) / 100,
                currency=currency,
                stripe_payment_intent_id=intent.id,
                status="pending",
                payment_metadata=metadata
            )
            db.session.add(payment)
            db.session.commit()

            return intent
        except stripe.error.StripeError as e:
            db.session.rollback()
            logger.error(f"Stripe Error: {str(e)}")
            raise e
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error creating payment intent: {str(e)}")
            raise e

    @staticmethod
    def handle_webhook(payload, sig_header):
        """
        Handles Stripe webhooks to update payment status.
        """
        api_key = StripeService._get_api_key()
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        try:
            if api_key and endpoint_secret:
                stripe.api_key = api_key
                event = stripe.Webhook.construct_event(
                    payload, sig_header, endpoint_secret
                )
            else:
                # Local smoke-test fallback: trust provided JSON payload shape.
                if isinstance(payload, (bytes, bytearray)):
                    payload = payload.decode("utf-8", errors="ignore")
                event = json.loads(payload or "{}")
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error(f"Webhook validation failed: {str(e)}")
            raise e

        # Log the event for audit trail
        try:
            webhook_event = StripeWebhookEvent(
                stripe_event_id=event['id'],
                event_type=event['type'],
                payload=event
            )
            db.session.add(webhook_event)
            db.session.flush() # Get ID without committing yet
        except Exception as e:
            logger.warning(f"Failed to log webhook event: {str(e)}")

        # Handle specific events
        try:
            from app.services.unified_payment_service import UnifiedPaymentService
        except Exception:
            UnifiedPaymentService = None
        
        try:
            if UnifiedPaymentService and event.get('type') == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                UnifiedPaymentService.update_payment_status(payment_intent.id, "succeeded", "stripe", event)
            elif UnifiedPaymentService and event.get('type') == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                UnifiedPaymentService.update_payment_status(payment_intent.id, "failed", "stripe", event)
            elif event.get('type') == 'payment_intent.succeeded':
                # Local fallback when UnifiedPaymentService is not available.
                payment_intent = event['data']['object']
                intent_id = payment_intent.get('id') if isinstance(payment_intent, dict) else None
                payment = PaymentStripe.query.filter_by(stripe_payment_intent_id=intent_id).first()
                if payment:
                    payment.status = "succeeded"
                    metadata = payment.payment_metadata or {}
                    booking_id = metadata.get('booking_id')
                    if booking_id:
                        try:
                            from app.models.booking import Booking, BookingStatus
                            from app.services.qr_code_service import qr_code_service

                            booking = Booking.query.get(booking_id)
                            if booking and booking.status != BookingStatus.CONFIRMED:
                                booking.status = BookingStatus.CONFIRMED
                                qr_code_service.generate_or_refresh(
                                    target_type="booking",
                                    target_id=booking.id,
                                    created_by=booking.user_id,
                                )
                        except Exception as booking_exc:
                            logger.warning(f"Booking confirmation/QR auto-generation skipped: {booking_exc}")
            elif event.get('type') == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                intent_id = payment_intent.get('id') if isinstance(payment_intent, dict) else None
                payment = PaymentStripe.query.filter_by(stripe_payment_intent_id=intent_id).first()
                if payment:
                    payment.status = "failed"
            
            if 'webhook_event' in locals():
                webhook_event.processed_at = db.func.now()
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing webhook event {event['type']}: {str(e)}")
            raise e

        return event

    @staticmethod
    def get_payment_by_intent_id(intent_id):
        return PaymentStripe.query.filter_by(stripe_payment_intent_id=intent_id).first()
