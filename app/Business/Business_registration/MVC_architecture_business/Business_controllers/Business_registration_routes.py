from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..Business_controllers.Business_controllers import (
    get_my_registration,
    register_business,
    update_my_registration,
)

business_bp = Blueprint(
    "business_registration",
    __name__,
    url_prefix="/api/v1/business/registrations",
)


@business_bp.route("", methods=["POST"])
@jwt_required()
def register_business_route():
    return register_business()


@business_bp.route("", methods=["GET"])
@jwt_required()
def get_my_registration_route():
    return get_my_registration()


@business_bp.route("/<string:request_id>", methods=["PATCH"])
@jwt_required()
def update_my_registration_route(request_id: str):
    return update_my_registration(request_id)

#submitting a new registration request, viewing the user's own registration request, and updating the user's own registration request. The admin routes for managing registration requests are defined in a separate file (Business_registration_routes_admin.py) to keep the user-facing and admin-facing functionalities organized and maintainable.
@business_bp.route("/registerrequest", methods=["POST"])
@jwt_required()
def submit_registration_request():
    return register_business()  

