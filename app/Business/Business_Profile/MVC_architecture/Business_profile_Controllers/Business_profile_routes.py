import uuid
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

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


def _resolve_user_id_for_register(payload: dict):
    """Resolve user id from JWT when available, else from request payload for testing."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity is not None:
            return uuid.UUID(str(identity)), None
    except Exception:
        pass

    raw_user_id = payload.get("user_id")
    if not raw_user_id:
        return None, (
            jsonify({
                "error": "Provide JWT token or user_id in request body for test mode."
            }),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        return uuid.UUID(str(raw_user_id)), None
    except (TypeError, ValueError):
        return None, (
            jsonify({"error": "user_id must be a valid UUID string."}),
            HTTPStatus.BAD_REQUEST,
        )


def _current_user_id_or_none():
    """Return JWT identity as UUID, or None when no JWT context exists."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity is None:
            return None
        return uuid.UUID(str(identity))
    except Exception:
        return None


@business_profile_blueprint.post("/register")
#@jwt_required()
def create_profile():
    """Create the authenticated user's business profile."""
    data = request.get_json(silent=True) or {}
    user_id, error_response = _resolve_user_id_for_register(data)
    if error_response is not None:
        return error_response

    data.pop("user_id", None)
    profile = create_business_profile(user_id, data)
    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.CREATED


@business_profile_blueprint.get("/me")
#@jwt_required()
def get_my_profile():
    """Get the authenticated user's business profile."""
    user_id = _current_user_id_or_none()
    if user_id is None:
        return jsonify({"error": "Authentication required."}), HTTPStatus.UNAUTHORIZED

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
#@jwt_required()
def patch_my_profile():
    """Update the authenticated user's business profile."""
    user_id = _current_user_id_or_none()
    if user_id is None:
        return jsonify({"error": "Authentication required."}), HTTPStatus.UNAUTHORIZED

    data = request.get_json(silent=True) or {}
    try:
        profile = update_business_profile(user_id, data)
    except ProfileNotFoundError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.NOT_FOUND

    return jsonify({"profile": {"id": str(profile.id)}}), HTTPStatus.OK




