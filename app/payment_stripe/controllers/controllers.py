from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.payment_stripe.views.views import StripeService
from app.payment_stripe.schemas import StripePaymentIntentSchema, StripePaymentResponseSchema
from app.utils.responses import ApiResponse
import stripe
import logging

logger = logging.getLogger(__name__)

payment_stripe_bp = Blueprint("payment_stripe_bp", __name__)

payment_intent_schema = StripePaymentIntentSchema()
payment_response_schema = StripePaymentResponseSchema()


def _current_user_id():
    try:
        return get_jwt_identity() or request.headers.get("X-User-Id")
    except RuntimeError:
        return request.headers.get("X-User-Id")

@payment_stripe_bp.route("/create-payment-intent", methods=["POST"])
# @jwt_required()  # TEMP: auth disabled for endpoint testing
def create_payment_intent():
    """
    Endpoint to create a PaymentIntent for Stripe.
    """
    data = request.get_json() or {}
    errors = payment_intent_schema.validate(data)
    if errors:
        return ApiResponse.error(
            message="Validation failed",
            code="VALIDATION_ERROR",
            details=errors,
            status_code=400
        )

    user_id = _current_user_id()
    try:
        intent = StripeService.create_payment_intent(
            user_id=user_id,
            amount=data["amount"],
            currency=data.get("currency", "usd"),
            metadata=data.get("metadata")
        )
        return ApiResponse.success(
            data={
                "clientSecret": intent.client_secret,
                "paymentIntentId": intent.id
            },
            message="Payment intent created successfully",
            status_code=201
        )
    except stripe.error.StripeError as e:
        return ApiResponse.error(
            message=str(e),
            code="STRIPE_ERROR",
            status_code=400
        )
    except (ValueError, RuntimeError) as e:
        return ApiResponse.error(
            message=str(e),
            code="BAD_REQUEST",
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        return ApiResponse.error(
            message="An unexpected error occurred while creating payment intent",
            code="INTERNAL_ERROR",
            status_code=500
        )

@payment_stripe_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    """
    Stripe webhook listener.
    """
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    if not sig_header:
        return ApiResponse.error(message="Missing Stripe-Signature header", code="WEBHOOK_ERROR", status_code=400)

    try:
        StripeService.handle_webhook(payload, sig_header)
        return ApiResponse.success(message="Webhook processed successfully")
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        return ApiResponse.error(message=f"Webhook verification failed: {str(e)}", code="WEBHOOK_VERIFICATION_FAILED", status_code=400)
    except RuntimeError as e:
        return ApiResponse.error(message=str(e), code="WEBHOOK_ERROR", status_code=400)
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return ApiResponse.error(message="Invalid webhook payload", code="WEBHOOK_ERROR", status_code=400)

@payment_stripe_bp.route("/payment-status/<intent_id>", methods=["GET"])
# @jwt_required()  # TEMP: auth disabled for endpoint testing
def get_payment_status(intent_id):
    """
    Check the status of a specific Stripe payment.
    """
    try:
        payment = StripeService.get_payment_by_intent_id(intent_id)
        if not payment:
            return ApiResponse.error(message="Payment not found", code="NOT_FOUND", status_code=404)
        
        # Simple ownership check
        current_user_id = _current_user_id()
        if current_user_id and str(payment.user_id) != str(current_user_id):
            return ApiResponse.error(message="Unauthorized access to payment record", code="UNAUTHORIZED", status_code=403)

        return ApiResponse.success(
            data=payment_response_schema.dump(payment),
            message="Payment status retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving payment status: {str(e)}")
        return ApiResponse.error(message="Internal error retrieving payment status", code="INTERNAL_ERROR", status_code=500)
