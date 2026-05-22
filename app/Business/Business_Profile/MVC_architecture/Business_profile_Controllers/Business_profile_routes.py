import uuid
import os
from werkzeug.exceptions import Unauthorized
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request
from app.utils.api_response import no_result

from app.Business.errors_handling import error_response
from app.Business.Business_registration.MVC_architecture_business.Business_controllers.Business_controllers import (
    register_business as register_business_request,
    get_my_registration,
    update_my_registration,
)
from app.Business.Business_registration.utils.utilities import role_required, jwt_or_dev_required

from ..Business_profile_views.Business_profile_services import (
    get_business_profile,
    get_business_profile_by_id,
    list_user_business_profiles,
    update_business_profile,
    delete_business_profile,
    ProfileNotFoundError,
)



business_bp = Blueprint(
    "business",
    __name__,
    url_prefix="/api/v1/business",
)

def _current_user_uuid() -> uuid.UUID:
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
    except Exception:
        identity = None

    if identity is None:
        identity = request.headers.get(
            "X-User-Id",
            os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"),
        )

    return uuid.UUID(str(identity))


@business_bp.route("/", methods=["POST"], strict_slashes=False)
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def register_business():
    return register_business_request()


@business_bp.route("/registrations", methods=["GET"])
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def get_my_business_registration():
    return get_my_registration()

# Note: The PATCH endpoint for updating the registration request is defined in the Business_registration_routes.py file, as it is more closely related to the registration process than the profile management.
@business_bp.route("/registrations/<string:request_id>", methods=["PATCH"])
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def patch_my_business_registration(request_id: str):
    return update_my_registration(request_id)


# The following endpoints are for managing the business profile, which is separate from the registration process. They require the user to have the "business_owner" role, which should be assigned after a successful registration and approval process.
@business_bp.route("/profiles", methods=["GET"])
# @role_required("business_owner")  # TEMP: auth disabled for endpoint testing
def get_my_profile():
    try:
        profile = get_business_profile(_current_user_uuid())
    except (ValueError, ProfileNotFoundError) as exc:
        return jsonify([]), HTTPStatus.OK

    return (
        jsonify(
            {
                "profile": {
                    "id": str(profile.id),
                    "user_id": str(profile.user_id),
                    "business_name": profile.business_name,
                    "business_type": profile.business_type,
                    "description": profile.description,
                    "address": profile.address,
                    "phone": profile.phone,
                    "email": profile.email,
                    "verified": profile.verified,
                    "is_active": profile.is_active,
                    "created_at": profile.created_at.isoformat() if profile.created_at else None,
                }
            }
        ),
        HTTPStatus.OK,
    )


@business_bp.route("/profiles/list", methods=["GET"])
# @role_required("business_owner")  # TEMP: auth disabled for endpoint testing
def list_my_profiles():
    profiles = list_user_business_profiles(_current_user_uuid())
    return (
        jsonify(
            {
                "profiles": [
                    {
                        "id": str(profile.id),
                        "user_id": str(profile.user_id),
                        "business_name": profile.business_name,
                        "business_type": profile.business_type,
                        "verified": profile.verified,
                        "is_active": profile.is_active,
                    }
                    for profile in profiles
                ]
            }
        ),
        HTTPStatus.OK,
    )


@business_bp.route("/profiles", methods=["PATCH"])
# @role_required("business_owner")  # TEMP: auth disabled for endpoint testing
def update_my_profile():
    payload = request.get_json(silent=True) or {}
    try:
        profile = update_business_profile(_current_user_uuid(), payload)
    except (ValueError, ProfileNotFoundError) as exc:
        return no_result("No business profile found; no changes applied")
    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.OK


@business_bp.route("/profiles/<string:profile_id>", methods=["PATCH"])
# @role_required("business_owner")  # TEMP: auth disabled for endpoint testing
def update_my_profile_by_id(profile_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        profile = update_business_profile(
            _current_user_uuid(),
            payload,
            profile_id=uuid.UUID(profile_id),
        )
    except (ValueError, ProfileNotFoundError) as exc:
        return no_result("Business profile not found; no changes applied")
    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.OK


@business_bp.route("/profiles/<string:profile_id>", methods=["DELETE"])
# @role_required("business_owner")  # TEMP: auth disabled for endpoint testing
def delete_business_profile_route(profile_id: str):
    try:
        delete_business_profile(_current_user_uuid(), uuid.UUID(str(profile_id)))
    except (ValueError, ProfileNotFoundError) as exc:
        return no_result("Business profile not found; nothing to delete")

    return jsonify({"message": "Business profile deleted successfully"}), HTTPStatus.OK


@business_bp.route("/attractions", methods=["GET"])
def get_business_attractions():
    """
    GET /api/v1/business/attractions
    Returns all attractions owned by the current user's business profile.
    """
    try:
        profile = get_business_profile(_current_user_uuid())
    except (ValueError, ProfileNotFoundError):
        return jsonify({"attractions": [], "total": 0}), HTTPStatus.OK

    from app.extensions import db
    from app.tourism_amenitties.attractions.models.attraction import Attraction
    from app.tourism_amenitties.attractions.schemas.attraction import AttractionSchema
    from sqlalchemy import select

    attractions = db.session.scalars(
        select(Attraction)
        .where(Attraction.business_owner_id == profile.id)
        .order_by(Attraction.created_at.desc())
    ).all()

    schema = AttractionSchema(many=True)
    return jsonify({"attractions": schema.dump(attractions), "total": len(attractions)}), HTTPStatus.OK


@business_bp.route("/bookings", methods=["GET"])
def get_business_bookings():
    """
    GET /api/v1/business/bookings
    Returns bookings for attractions owned by the current user's business profile.
    """
    try:
        profile = get_business_profile(_current_user_uuid())
    except (ValueError, ProfileNotFoundError):
        return jsonify({"bookings": [], "total": 0}), HTTPStatus.OK

    from app.extensions import db
    from app.tourism_amenitties.attractions.models.attraction import Attraction
    from sqlalchemy import select

    attraction_ids = db.session.scalars(
        select(Attraction.id).where(Attraction.business_owner_id == profile.id)
    ).all()

    if not attraction_ids:
        return jsonify({"bookings": [], "total": 0}), HTTPStatus.OK

    try:
        from app.models.booking import Booking, BookingItem
        from app.validators.schemas import BookingSchema, BookingItemSchema

        booking_ids = db.session.scalars(
            select(BookingItem.booking_id)
            .where(BookingItem.target_id.in_(attraction_ids))
            .distinct()
        ).all()

        if not booking_ids:
            return jsonify({"bookings": [], "total": 0}), HTTPStatus.OK

        bookings = db.session.scalars(
            select(Booking)
            .where(Booking.id.in_(booking_ids))
            .order_by(Booking.created_at.desc())
        ).all()

        _booking_schema = BookingSchema()
        _item_schema = BookingItemSchema()

        result = []
        for b in bookings:
            bd = _booking_schema.dump(b)
            relevant_items = [
                _item_schema.dump(i)
                for i in b.items
                if i.target_id in attraction_ids
            ]
            bd["items"] = relevant_items
            result.append(bd)

        return jsonify({"bookings": result, "total": len(result)}), HTTPStatus.OK

    except Exception as exc:
        # Fallback: booking feature may not be available in all envs
        return jsonify({"bookings": [], "total": 0, "error": str(exc)}), HTTPStatus.OK
