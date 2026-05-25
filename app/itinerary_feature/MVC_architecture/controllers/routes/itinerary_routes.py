"""
Routes — Itinerary Blueprint
Mount: app.register_blueprint(itinerary_bp, url_prefix='/api/v1')
"""

from flask               import Blueprint

from app.itinerary_feature.MVC_architecture.controllers.itinerary_controller import (
    create,
    list_itineraries,
    show,
    update,
    destroy,
    publish,
    generate_qr,
    scan_redirect,
)
from app.itinerary_feature.MVC_architecture.controllers.itinerary_days_controller import (
    add_day,
    update_day,
    remove_day,
    add_attraction_to_day,
    remove_attraction_from_day,
)

itinerary_bp = Blueprint("itineraries", __name__)

# ── Authenticated ─────────────────────────────────────────────────────────────
itinerary_bp.add_url_rule(
    "/itineraries",
    view_func=create,
    methods=["POST"],
)
itinerary_bp.add_url_rule(
    "/itineraries",
    view_func=list_itineraries,
    methods=["GET"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>",
    view_func=show,
    methods=["GET"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>",
    view_func=update,
    methods=["PATCH"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>",
    view_func=destroy,
    methods=["DELETE"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>/publish",
    view_func=publish,
    methods=["POST"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>/qr",
    view_func=generate_qr,
    methods=["POST"],
)

# ── Days management ───────────────────────────────────────────────────────────
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>/days",
    view_func=add_day,
    methods=["POST"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>/days/<uuid:day_id>",
    view_func=update_day,
    methods=["PATCH"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>/days/<uuid:day_id>",
    view_func=remove_day,
    methods=["DELETE"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>/days/<uuid:day_id>/attractions",
    view_func=add_attraction_to_day,
    methods=["POST"],
)
itinerary_bp.add_url_rule(
    "/itineraries/<uuid:itinerary_id>/days/<uuid:day_id>/attractions/<uuid:entry_id>",
    view_func=remove_attraction_from_day,
    methods=["DELETE"],
)

# ── Public (no auth) ──────────────────────────────────────────────────────────
itinerary_bp.add_url_rule(
    "/public/itineraries/<string:token>",
    view_func=scan_redirect,
    methods=["GET"],
)
