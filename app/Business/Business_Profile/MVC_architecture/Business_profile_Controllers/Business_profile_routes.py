from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..Business_profile_views.Business_profile_services import (
    create_business_profile,
    get_business_profile,
    update_business_profile,
    ProfileNotFoundError,
)


business_profile_blueprint = Blueprint(
    "business_profile",
    __name__,
    url_prefix="/api/v1/business/business_profiles",
)


@business_profile_blueprint.post("/register")
@jwt_required()
def create_profile():
    """Create the authenticated user's business profile."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    profile = create_business_profile(user_id, data)
    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.CREATED


@business_profile_blueprint.get("/me")
@jwt_required()
def get_my_profile():
    """Get the authenticated user's business profile."""
    user_id = get_jwt_identity()
    try:
        profile = get_business_profile(user_id)
    except ProfileNotFoundError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.NOT_FOUND

    return (
        jsonify(
            {
                "profile": {
                    "id": str(profile.id),
                    "business_name": profile.business_name,
                    "business_type": profile.business_type,
                    "phone": profile.phone,
                    "email": profile.email,
                    "address": profile.address,
                    "description": profile.description,
                    "verified": profile.verified,
                    "is_active": profile.is_active,
                }
            }
        ),
        HTTPStatus.OK,
    )


@business_profile_blueprint.patch("/me")
@jwt_required()
def patch_my_profile():
    """Update the authenticated user's business profile."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    try:
        profile = update_business_profile(user_id, data)
    except ProfileNotFoundError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.NOT_FOUND

    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.OK




