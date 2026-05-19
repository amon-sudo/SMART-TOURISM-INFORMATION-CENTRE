"""
Routes — Handoff Blueprint
Mount: app.register_blueprint(handoff_bp, url_prefix='/api/v1')

Three routes:

  POST /api/v1/sessions/<kiosk_session_id>/handoff
      Kiosk creates a handoff QR. Requires JWT (kiosk service account).

  GET  /api/v1/handoff/<token>
      Phone scans the QR. No auth — token IS the credential.
      Burns on first use.

  GET  /api/v1/sessions/<kiosk_session_id>/handoff-status
      Kiosk polls to know when the phone has scanned.
      Requires JWT (same kiosk service account).
"""

from flask import Blueprint
from app.qr_code.MVC_architecture.controllers.handoff_controller import (
    create_handoff,
    redeem_handoff,
    handoff_status,
)

handoff_bp = Blueprint("handoff", __name__)

# Kiosk: generate handoff QR
handoff_bp.add_url_rule(
    "/sessions/<uuid:kiosk_session_id>/handoff",
    view_func=create_handoff,
    methods=["POST"],
)

# Phone: scan QR — no auth wrapper, token is the credential
handoff_bp.add_url_rule(
    "/handoff/<string:token>",
    view_func=redeem_handoff,
    methods=["GET"],
)

# Kiosk: poll for transfer confirmation
handoff_bp.add_url_rule(
    "/sessions/<uuid:kiosk_session_id>/handoff-status",
    view_func=handoff_status,
    methods=["GET"],
)
