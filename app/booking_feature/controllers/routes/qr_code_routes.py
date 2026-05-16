"""
Routes — QR Code Blueprint
Mount: app.register_blueprint(qr_bp, url_prefix='/api/v1')
"""

from flask              import Blueprint
from flask_jwt_extended import jwt_required

from app.booking_feature.controllers.qr_code_controller import (
    list_qr_codes,
    show_qr_code,
    revoke,
    regenerate,
    scan,
)
from app.booking_feature.middleware.require_admin import admin_required

qr_bp = Blueprint("booking_qr_codes", __name__)

# ── Public scan handler (no auth) ─────────────────────────────────────────────
qr_bp.add_url_rule(
    "/public/qr/<string:token>/scan",
    view_func=scan,
    methods=["GET"],
)

# ── Admin ─────────────────────────────────────────────────────────────────────
qr_bp.add_url_rule(
    "/admin/qr-codes",
    view_func=list_qr_codes,
    methods=["GET"],
)
qr_bp.add_url_rule(
    "/admin/qr-codes/<uuid:qr_id>",
    view_func=show_qr_code,
    methods=["GET"],
)
qr_bp.add_url_rule(
    "/admin/qr-codes/<uuid:qr_id>/revoke",
    view_func=revoke,
    methods=["POST"],
)
qr_bp.add_url_rule(
    "/admin/qr-codes/<uuid:qr_id>/regenerate",
    view_func=regenerate,
    methods=["POST"],
)
