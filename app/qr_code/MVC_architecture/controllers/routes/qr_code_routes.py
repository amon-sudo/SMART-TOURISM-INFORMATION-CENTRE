"""
Routes — QR Code Blueprint
Mount: app.register_blueprint(qr_bp, url_prefix='/api/v1')
"""

from flask              import Blueprint
from flask_jwt_extended import jwt_required

from app.qr_code.MVC_architecture.controllers.qr_code_controller import (
    list_qr_codes,
    show_qr_code,
    revoke,
    regenerate,
    scan,
)
from app.qr_code.middleware.require_admin import admin_required

qr_bp = Blueprint("qr_codes", __name__)

# ── Public scan handler (no auth) ─────────────────────────────────────────────
qr_bp.add_url_rule(
    "/public/qr/<string:token>/scan",
    view_func=scan,
    methods=["GET"],
)

# ── Admin ─────────────────────────────────────────────────────────────────────
qr_bp.add_url_rule(
    "/admin/qr-codes",
    view_func=admin_required(list_qr_codes),
    methods=["GET"],
)
qr_bp.add_url_rule(
    "/admin/qr-codes/<uuid:qr_id>",
    view_func=admin_required(show_qr_code),
    methods=["GET"],
)
qr_bp.add_url_rule(
    "/admin/qr-codes/<uuid:qr_id>/revoke",
    view_func=admin_required(revoke),
    methods=["POST"],
)
qr_bp.add_url_rule(
    "/admin/qr-codes/<uuid:qr_id>/regenerate",
    view_func=admin_required(regenerate),
    methods=["POST"],
)
