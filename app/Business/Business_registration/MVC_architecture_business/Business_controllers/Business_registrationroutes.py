from flask import Blueprint
from flask_jwt_extended import jwt_required

from .Business_controllers import (
    register_business,
    get_my_registration,
    update_my_registration,
)


business_bp = Blueprint("business", __name__, url_prefix="/api/v1/business")

# POST /api/v1/business/register
business_bp.add_url_rule(
    "/register",
    #view_func=jwt_required()(register_business),
    view_func=register_business,
    methods=["POST"],
)

# GET  /api/v1/business/registration
# PATCH /api/v1/business/registration/<request_id>
# Business owners (and applicants) manage their own registration.
business_bp.add_url_rule(
    "/registration",
    #view_func=jwt_required()(get_my_registration),
    view_func=get_my_registration,
    methods=["GET"],
)
business_bp.add_url_rule(
    "/registration/<string:request_id>",
    #view_func=jwt_required()(update_my_registration),
    view_func=update_my_registration,
    methods=["PATCH"],
)
