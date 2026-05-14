from flask import Blueprint, jsonify, request
from app.Business.Business_registration.utils.utilities import jwt_or_dev_required


from ..Business_controllers.Business_controllers import (
    delete_my_registration,
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
@business_bp.route("/register", methods=["POST"])
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def register_business_route():
    return register_business()


@business_bp.route("", methods=["GET"])
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def get_my_registration_route():
    return get_my_registration()


@business_bp.route("/<string:request_id>", methods=["PATCH"])
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def update_my_registration_route(request_id: str):
    return update_my_registration(request_id)

#businesses to delete their pending registration request if they change their mind or need to correct something before resubmitting. This endpoint allows for better user control and flexibility in managing their registration process, while still ensuring that only the owner of the request can perform this action.
@business_bp.route("/registration/<string:request_id>", methods=["DELETE"])
# @jwt_or_dev_required()  # TEMP: auth disabled for endpoint testing
def delete_my_registration_request(request_id: str):
    return delete_my_registration(request_id)
