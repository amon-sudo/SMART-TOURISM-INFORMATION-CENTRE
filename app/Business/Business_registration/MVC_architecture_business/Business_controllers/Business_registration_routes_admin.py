from flask import Blueprint

from .Business_controllers import (
    admin_list_registrations,
    admin_get_registration,
    admin_action_registration,
)
from ...utils.utilities import admin_required


business_admin_bp = Blueprint(
    "business_admin",
    __name__,
    url_prefix="/api/v1/admin/business/registrations",
)


# GET /api/v1/admin/business/registrations
@business_admin_bp.get("/all_registrations")
#@admin_required()
def list_registrations_admin():
    return admin_list_registrations()


# GET /api/v1/admin/business/registrations/<request_id>
@business_admin_bp.get("/<string:request_id>")
#@admin_required()
def get_registration_admin(request_id: str):
    return admin_get_registration(request_id)


# PATCH /api/v1/admin/business/registrations/<request_id>
# Approve / reject / suspend
@business_admin_bp.patch("/<string:request_id>")
#@admin_required()
def action_registration_admin(request_id: str):
    return admin_action_registration(request_id)


