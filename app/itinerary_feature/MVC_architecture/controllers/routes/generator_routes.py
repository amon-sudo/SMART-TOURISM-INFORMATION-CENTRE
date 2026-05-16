"""
Routes — Itinerary Generator Blueprint
Mount: app.register_blueprint(generator_bp, url_prefix='/api/v1')
"""

from flask              import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.itinerary_generator_controller import (
    generate_itinerary,
    submit_operator_time_data,
    ingest_visit_duration,
)
from app.middleware.require_admin import admin_required

generator_bp = Blueprint("generator", __name__)

# ── Tourist: generate itinerary ───────────────────────────────────────────────
# jwt_required so the itinerary is linked to a user; also works for
# kiosk sessions where the kiosk authenticates as a service user
generator_bp.add_url_rule(
    "/itineraries/generate",
    view_func=jwt_required()(generate_itinerary),
    methods=["POST"],
)

# ── Operator: submit visit duration for an attraction ─────────────────────────
generator_bp.add_url_rule(
    "/admin/attractions/<uuid:attraction_id>/time-data",
    view_func=admin_required(submit_operator_time_data),
    methods=["POST"],
)

# ── Internal analytics pipeline ───────────────────────────────────────────────
# Secured by admin_required; called by the analytics event processor,
# not by tourists directly
generator_bp.add_url_rule(
    "/internal/analytics/visit-duration",
    view_func=admin_required(ingest_visit_duration),
    methods=["POST"],
)
