import uuid
import os
from werkzeug.exceptions import Unauthorized
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

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
        identity = get_jwt_identity()
    except RuntimeError:
        identity = None

    if identity is None:
        identity = request.headers.get(
            "X-User-Id",
            os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"),
        )

    return uuid.UUID(str(identity))


@business_bp.route("/register", methods=["POST"], strict_slashes=False)
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def register_business():
    return register_business_request()


@business_bp.route("/registration", methods=["GET"])
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def get_my_business_registration():
    return get_my_registration()

# Note: The PATCH endpoint for updating the registration request is defined in the Business_registration_routes.py file, as it is more closely related to the registration process than the profile management.
@business_bp.route("/registration/<string:request_id>", methods=["PATCH"])
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def patch_my_business_registration(request_id: str):
    return update_my_registration(request_id)


# The following endpoints are for managing the business profile, which is separate from the registration process. They require the user to have the "business_owner" role, which should be assigned after a successful registration and approval process.
@business_bp.route("/profile", methods=["GET"])
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
                    "verified": profile.verified,
                    "is_active": profile.is_active,
                }
            }
        ),
        HTTPStatus.OK,
    )


@business_bp.route("/profiles", methods=["GET"])
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


@business_bp.route("/profile", methods=["PATCH"])
# @role_required("business_owner")  # TEMP: auth disabled for endpoint testing
def update_my_profile():
    payload = request.get_json(silent=True) or {}
    try:
        profile = update_business_profile(_current_user_uuid(), payload)
    except (ValueError, ProfileNotFoundError) as exc:
        return error_response(str(exc), status_code=HTTPStatus.NOT_FOUND, code="PROFILE_NOT_FOUND")
    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.OK


@business_bp.route("/profile/<string:profile_id>", methods=["PATCH"])
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
        return error_response(str(exc), status_code=HTTPStatus.NOT_FOUND, code="PROFILE_NOT_FOUND")
    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.OK

#businesses to be able to update thier own profiles
@business_bp.route("/profile/update", methods=["PATCH"])
# @role_required("business_owner")  # TEMP: auth disabled for endpoint testing
def update_business_profile_route():
    payload = request.get_json(silent=True) or {}
    try:
        profile = update_business_profile(_current_user_uuid(), payload)
    except (ValueError, ProfileNotFoundError) as exc:
        return error_response(str(exc), status_code=HTTPStatus.NOT_FOUND, code="PROFILE_NOT_FOUND")
    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.OK

#businesses to be able to delete thier own profiles (soft delete by setting is_active to False)
@business_bp.route("/profile/delete", methods=["PATCH"])
# @role_required("business_owner")  # TEMP: auth disabled for endpoint testing
def delete_business_profile_route():
    payload = request.get_json(silent=True) or {}
    profile_id = payload.get("profile_id")
    if not profile_id:
        return error_response(
            "profile_id is required.",
            status_code=HTTPStatus.BAD_REQUEST,
            code="MISSING_FIELD",
            details={"field": "profile_id"},
        )

    try:
        delete_business_profile(_current_user_uuid(), uuid.UUID(str(profile_id)))
    except (ValueError, ProfileNotFoundError) as exc:
        return error_response(str(exc), status_code=HTTPStatus.NOT_FOUND, code="PROFILE_NOT_FOUND")

    return jsonify({"message": "Business profile deleted successfully"}), HTTPStatus.OK