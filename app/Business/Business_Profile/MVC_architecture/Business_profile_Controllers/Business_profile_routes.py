import uuid
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.Business.Business_registration.MVC_architecture_business.Business_controllers.Business_controllers import (
    register_business as register_business_request,
    get_my_registration,
    update_my_registration,
)
from app.Business.Business_registration.utils.utilities import role_required

from ..Business_profile_views.Business_profile_services import (
    get_business_profile,
    update_business_profile,
    ProfileNotFoundError,
)



business_bp = Blueprint(
    "business",
    __name__,
    url_prefix="/api/v1/business",
)

def _current_user_uuid() -> uuid.UUID:
    identity = get_jwt_identity()
    return uuid.UUID(str(identity))


@business_bp.route("/register", methods=["POST"], strict_slashes=False)
@jwt_required()
def register_business():
    return register_business_request()


@business_bp.route("/registration", methods=["GET"])
@jwt_required()
def get_my_business_registration():
    return get_my_registration()

# Note: The PATCH endpoint for updating the registration request is defined in the Business_registration_routes.py file, as it is more closely related to the registration process than the profile management.
@business_bp.route("/registration/<string:request_id>", methods=["PATCH"])
@jwt_required()
def patch_my_business_registration(request_id: str):
    return update_my_registration(request_id)


# The following endpoints are for managing the business profile, which is separate from the registration process. They require the user to have the "business_owner" role, which should be assigned after a successful registration and approval process.

@business_bp.route("/profile", methods=["GET"])
@role_required("business_owner")
def get_my_profile():
    try:
        profile = get_business_profile(_current_user_uuid())
    except (ValueError, ProfileNotFoundError) as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.NOT_FOUND

    return (
        jsonify(
            {
                "profile": {
                    "id": str(profile.id),
                    "user_id": str(profile.user_id),
                    "business_name": profile.business_name,
                    "business_type": profile.business_type,
                    "verified": profile.verified,
                    "is_active": profile.is_active,
                }
            }
        ),
        HTTPStatus.OK,
    )


@business_bp.route("/profile", methods=["PATCH"])
@role_required("business_owner")
def update_my_profile():
    payload = request.get_json(silent=True) or {}
    try:
        profile = update_business_profile(_current_user_uuid(), payload)
    except (ValueError, ProfileNotFoundError) as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.NOT_FOUND

    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.OK

