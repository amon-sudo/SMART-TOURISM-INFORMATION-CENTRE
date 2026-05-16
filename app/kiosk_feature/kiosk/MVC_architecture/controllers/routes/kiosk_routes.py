"""
Routes — Kiosk Blueprints
Three blueprints, registered separately in app/__init__.py:

  kiosk_bp      — device registry (admin)
  session_bp    — session lifecycle (kiosk frontend + admin)
  transfer_bp   — session-to-phone transfer (kiosk frontend + phone)

Mount in app/__init__.py:
  app.register_blueprint(kiosk_bp,    url_prefix="/api")
  app.register_blueprint(session_bp,  url_prefix="/api")
  app.register_blueprint(transfer_bp, url_prefix="/api")
"""

from flask              import Blueprint

from app.controllers.kiosk_controllers import (
    # Kiosk device
    register_kiosk, list_kiosks, show_kiosk,
    update_kiosk, decommission_kiosk,
    receive_heartbeat, receive_health_event,
    sync_content, get_offline_content, get_analytics,
    # Session
    start_session, update_session_state,
    end_session, log_analytics_event,
    # Transfer
    create_transfer, redeem_transfer, get_transfer_status,
)
from app.middleware.require_admin import admin_required


# ══════════════════════════════════════════════════════════════════════════════
#  KIOSK DEVICE BLUEPRINT
# ══════════════════════════════════════════════════════════════════════════════
kiosk_bp = Blueprint("kiosks", __name__)

# Admin: device registry
kiosk_bp.add_url_rule(
    "/admin/kiosks",
    view_func=register_kiosk,
    methods=["POST"],
)
kiosk_bp.add_url_rule(
    "/admin/kiosks",
    view_func=list_kiosks,
    methods=["GET"],
)
kiosk_bp.add_url_rule(
    "/admin/kiosks/<uuid:kiosk_id>",
    view_func=show_kiosk,
    methods=["GET"],
)
kiosk_bp.add_url_rule(
    "/admin/kiosks/<uuid:kiosk_id>",
    view_func=update_kiosk,
    methods=["PATCH"],
)
kiosk_bp.add_url_rule(
    "/admin/kiosks/<uuid:kiosk_id>/decommission",
    view_func=decommission_kiosk,
    methods=["POST"],
)
kiosk_bp.add_url_rule(
    "/admin/kiosks/<uuid:kiosk_id>/analytics",
    view_func=get_analytics,
    methods=["GET"],
)
kiosk_bp.add_url_rule(
    "/admin/kiosks/<uuid:kiosk_id>/content-sync",
    view_func=sync_content,
    methods=["POST"],
)

# Kiosk agent: heartbeat + health events + offline content
# These use jwt_required — the kiosk agent authenticates as a service account
kiosk_bp.add_url_rule(
    "/kiosks/<uuid:kiosk_id>/heartbeat",
    view_func=receive_heartbeat,
    methods=["POST"],
)
kiosk_bp.add_url_rule(
    "/kiosks/<uuid:kiosk_id>/health-events",
    view_func=receive_health_event,
    methods=["POST"],
)
kiosk_bp.add_url_rule(
    "/kiosks/<uuid:kiosk_id>/content/<string:content_type>",
    view_func=get_offline_content,
    methods=["GET"],
)


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION BLUEPRINT
# ══════════════════════════════════════════════════════════════════════════════
session_bp = Blueprint("sessions", __name__)

# Session lifecycle (kiosk frontend authenticates with kiosk JWT)
session_bp.add_url_rule(
    "/kiosks/<uuid:kiosk_id>/sessions",
    view_func=start_session,
    methods=["POST"],
)
session_bp.add_url_rule(
    "/sessions/<uuid:session_id>/state",
    view_func=update_session_state,
    methods=["PATCH"],
)
session_bp.add_url_rule(
    "/sessions/<uuid:session_id>/end",
    view_func=end_session,
    methods=["POST"],
)

# Analytics event ingestion (high-frequency — called on every tourist tap)
session_bp.add_url_rule(
    "/sessions/<uuid:session_id>/events",
    view_func=log_analytics_event,
    methods=["POST"],
)


# ══════════════════════════════════════════════════════════════════════════════
#  TRANSFER BLUEPRINT
# ══════════════════════════════════════════════════════════════════════════════
transfer_bp = Blueprint("transfers", __name__)

# Kiosk: generate transfer QR
transfer_bp.add_url_rule(
    "/sessions/<uuid:session_id>/transfer",
    view_func=create_transfer,
    methods=["POST"],
)

# Phone: scan QR — NO auth, token is the credential
transfer_bp.add_url_rule(
    "/sessions/transfer/<string:token>",
    view_func=redeem_transfer,
    methods=["GET"],
)

# Kiosk: poll for transfer confirmation
transfer_bp.add_url_rule(
    "/sessions/<uuid:session_id>/transfer-status",
    view_func=get_transfer_status,
    methods=["GET"],
)
