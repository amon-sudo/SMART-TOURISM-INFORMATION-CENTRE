from http import HTTPStatus
import uuid

from flask import Blueprint, jsonify, request

from app.Business.errors_handling import error_response
from app.Business.Business_Profile.MVC_architecture.Business_profile_models.Business_profile_schema.business_profile_schema import BusinessProfileAdminResponseSchema
from app.Business.Business_registration.MVC_architecture_business.Business_controllers.Business_controllers import admin_action_registration, admin_get_registration, admin_list_registrations

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


_admin_profile_schema = BusinessProfileAdminResponseSchema()

@business_admin_blueprint.route("/registrations", methods=["GET"])
@admin_required()
def admin_list_registration_requests():
    return admin_list_registrations()


@business_admin_blueprint.route("/registrations/<string:request_id>", methods=["GET"])
@admin_required()
def admin_get_registration_request(request_id: str):
    return admin_get_registration(request_id)


@business_admin_blueprint.route("/registrations/<string:request_id>", methods=["PATCH"])
@admin_required()
def admin_update_registration_request(request_id: str):
    return admin_action_registration(request_id)


@business_admin_blueprint.route("/profiles", methods=["GET"])
@admin_required()
def admin_list_profiles():
    search_query = request.args.get("search", type=str)
    profiles = get_all_business_profiles(public=False, search_query=search_query)
    return jsonify([_admin_profile_schema.dump(p) for p in profiles]), HTTPStatus.OK


@business_admin_blueprint.route("/profiles/<string:profile_id>", methods=["GET"])
@admin_required()
def admin_get_profile(profile_id: str):
    try:
        profile = get_business_profile_by_id(uuid.UUID(profile_id), public=False)
    except (ValueError, ProfileNotFoundError) as exc:
        return jsonify([]), HTTPStatus.OK

    return jsonify({"profile": _admin_profile_schema.dump(profile)}), HTTPStatus.OK
