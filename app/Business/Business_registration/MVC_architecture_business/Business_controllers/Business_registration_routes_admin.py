from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.Business.Business_registration.utils.utilities import admin_required
from ..Business_controllers.Business_controllers import (
    admin_action_registration,
    admin_get_registration,
    admin_list_registrations,
)

business_admin_blueprint = Blueprint(
    "business_admin_registration",
    __name__,
    url_prefix="/api/v1/admin/business/registrations",
)


@business_admin_blueprint.route("", methods=["GET"])
@business_admin_blueprint.route("/all_registrations", methods=["GET"])
# @admin_required()  # TEMP: auth disabled for endpoint testing
def list_registrations():
    return admin_list_registrations()


@business_admin_blueprint.route("/<string:request_id>", methods=["GET"])
# @admin_required()  # TEMP: auth disabled for endpoint testing
def get_registration(request_id: str):
    return admin_get_registration(request_id)


@business_admin_blueprint.route("/<string:request_id>", methods=["PATCH"])
# @admin_required()  # TEMP: auth disabled for endpoint testing
def action_registration(request_id: str):
    return admin_action_registration(request_id)