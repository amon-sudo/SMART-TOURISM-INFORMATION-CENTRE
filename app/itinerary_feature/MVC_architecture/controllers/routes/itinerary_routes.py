"""
Routes — Itinerary Blueprint
Mount: app.register_blueprint(itinerary_bp, url_prefix='/api/v1')
"""

from flask               import Blueprint
from flask_jwt_extended  import jwt_required

from app.controllers.itinerary_controller import (
    create,
    list_itineraries,
    show,
    update,
    destroy,
    publish,
    generate_qr,
    scan_redirect,
)

itinerary_bp = Blueprint("itineraries", __name__)

# ── Authenticated ─────────────────────────────────────────────────────────────
itinerary_bp.add_url_rule(
    "/itineraries",
    view_func=jwt_required()(create),
    methods=["POST"],
)
itinerary_bp.add_url_rule(
    "/itineraries",
    view_func=jwt_required()(list_itineraries),
    methods=["GET"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>",
    view_func=jwt_required()(show),
    methods=["GET"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>",
    view_func=jwt_required()(update),
    methods=["PATCH"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>",
    view_func=jwt_required()(destroy),
    methods=["DELETE"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>/publish",
    view_func=jwt_required()(publish),
    methods=["POST"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>/qr",
    view_func=jwt_required()(generate_qr),
    methods=["POST"],
)

# ── Public (no auth) ──────────────────────────────────────────────────────────
itinerary_bp.add_url_rule(
    "/public/itineraries/<string:token>",
    view_func=scan_redirect,
    methods=["GET"],
)
