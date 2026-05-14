from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.unified_payment_service import UnifiedPaymentService
from app.utils.responses import ApiResponse
import logging

logger = logging.getLogger(__name__)

unified_payment_bp = Blueprint("unified_payment_bp", __name__)

@unified_payment_bp.route("/pay", methods=["POST"])
@jwt_required()
def pay():
    """
    Unified payment endpoint.
    Expects: { "booking_id": "...", "provider": "stripe|mpesa", "amount": 100, ... }
    """
    data = request.get_json() or {}
    user_id = get_jwt_identity()
    
    booking_id = data.get("booking_id")
    provider = data.get("provider")
    amount = data.get("amount")

    if not all([booking_id, provider, amount]):
        return ApiResponse.error(
            message="Missing required fields: booking_id, provider, and amount are mandatory.",
            code="MISSING_FIELDS",
            status_code=400
        )

    try:
        result = UnifiedPaymentService.initiate_payment(
            booking_id=booking_id,
            provider=provider,
            user_id=user_id,
            amount=amount,
            **data
        )
        return ApiResponse.success(
            data=result,
            message=f"Payment via {provider} initiated successfully.",
            status_code=201
        )
    except ValueError as e:
        return ApiResponse.error(
            message=str(e),
            code="PAYMENT_INITIATION_FAILED",
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error in unified payment initiation: {str(e)}")
        return ApiResponse.error(
            message="An unexpected error occurred while processing your payment request.",
            code="INTERNAL_ERROR",
            status_code=500
        )
