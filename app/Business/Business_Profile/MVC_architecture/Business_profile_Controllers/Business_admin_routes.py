from http import HTTPStatus

from flask import Blueprint, jsonify

from ..Business_profile_views.Business_profile_services import (
    get_all_business_profiles,
    get_business_profile_by_id,
    ProfileNotFoundError,
)
from ....Business_registration.utils.utilities import admin_required


business_admin_blueprint = Blueprint(
    "business_admin_profile",
    __name__,
    url_prefix="/api/v1/admin/business/business_profiles",
)


@business_admin_blueprint.get("/all_profiles")
@admin_required()
def admin_get_profiles():
    """Admin: list all business profiles."""
    profiles = get_all_business_profiles(public=False)
    payload = [
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
    return jsonify({"profiles": payload}), HTTPStatus.OK


@business_admin_blueprint.get("/<string:profile_id>")
@admin_required()
def admin_get_profile(profile_id: str):
    """Admin: fetch a single business profile by ID."""
    import uuid

    try:
        profile = get_business_profile_by_id(uuid.UUID(profile_id), public=False)
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
    
