"""
Routes — Booking Blueprint
Mount: app.register_blueprint(booking_bp, url_prefix='/api/v1')
"""

from flask              import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.booking_controller import (
    create,
    list_bookings,
    show,
    cancel,
    generate_qr,
    admin_list,
)
from app.middleware.require_admin import admin_required

booking_bp = Blueprint("bookings", __name__)

# ── Authenticated ─────────────────────────────────────────────────────────────
booking_bp.add_url_rule(
    "/bookings",
    view_func=jwt_required()(create),
    methods=["POST"],
)
booking_bp.add_url_rule(
    "/bookings",
    view_func=jwt_required()(list_bookings),
    methods=["GET"],
)
booking_bp.add_url_rule(
    "/bookings/<uuid:booking_id>",
    view_func=jwt_required()(show),
    methods=["GET"],
)
booking_bp.add_url_rule(
    "/bookings/<uuid:booking_id>/cancel",
    view_func=jwt_required()(cancel),
    methods=["PATCH"],
)
booking_bp.add_url_rule(
    "/bookings/<uuid:booking_id>/qr",
    view_func=jwt_required()(generate_qr),
    methods=["POST"],
)

# ── Admin ─────────────────────────────────────────────────────────────────────
booking_bp.add_url_rule(
    "/admin/bookings",
    view_func=admin_required(admin_list),
    methods=["GET"],
)
