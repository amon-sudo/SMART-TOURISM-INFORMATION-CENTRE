import stripe
import os
import logging
import uuid
from decimal import Decimal
from app.extensions import db
from app.payment_stripe.models.models import PaymentStripe, StripeWebhookEvent

# Configure logging
logger = logging.getLogger(__name__)

class StripeService:
    @staticmethod
    def _get_api_key():
        key = os.getenv("STRIPE_SECRET_KEY")
        if not key:
            logger.error("STRIPE_SECRET_KEY is not set in environment variables.")
            raise RuntimeError("Stripe API key is missing.")
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

        stripe.api_key = StripeService._get_api_key()
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata,
                automatic_payment_methods={"enabled": True},
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
        stripe.api_key = StripeService._get_api_key()
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not endpoint_secret:
            logger.error("STRIPE_WEBHOOK_SECRET is not set.")
            raise RuntimeError("Webhook secret is missing.")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
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
        from app.services.unified_payment_service import UnifiedPaymentService
        
        try:
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                UnifiedPaymentService.update_payment_status(payment_intent.id, "succeeded", "stripe", event)
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                UnifiedPaymentService.update_payment_status(payment_intent.id, "failed", "stripe", event)
            
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
