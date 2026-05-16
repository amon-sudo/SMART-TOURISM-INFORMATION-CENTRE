"""
Itinerary Generator Controller
Exposes two endpoints:

  POST /api/itineraries/generate
      Tourist-facing: accepts preferences, triggers AI generation,
      returns a fully built itinerary with QR code.

  POST /api/admin/attractions/<attraction_id>/time-data
      Operator-facing: submit known visit duration for an attraction.

  POST /api/internal/analytics/visit-duration
      Internal analytics pipeline: ingest a check-in/check-out event pair.
"""

from __future__ import annotations

import uuid

from flask               import request
from flask_jwt_extended  import get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import text

from app.extensions                         import db
from app.services.itinerary_generator_service import itinerary_generator_service
from app.services.attraction_time_data_service import attraction_time_data_service
from app.validators.generator_schemas          import (
    GenerateItinerarySchema,
    OperatorTimeDataSchema,
    AnalyticsVisitSchema,
)
from app.utils.api_response import success, created, bad_request, no_result


# ── Schema instances ──────────────────────────────────────────────────────────
_generate_schema      = GenerateItinerarySchema()
_operator_time_schema = OperatorTimeDataSchema()
_analytics_schema     = AnalyticsVisitSchema()


def _current_user_uuid():
    try:
        identity = get_jwt_identity()
    except Exception:
        identity = request.headers.get("X-User-Id")

    if identity in (None, "", "None"):
        identity = "00000000-0000-0000-0000-000000000001"

    if isinstance(identity, uuid.UUID):
        return identity
    return uuid.UUID(str(identity))


# ─── Tourist: generate itinerary ──────────────────────────────────────────────

def generate_itinerary():
    """
    POST /api/itineraries/generate

    Body:
    {
      "duration_days":          5,
      "interests":              ["wildlife", "museum", "cultural"],
      "budget_level":           "medium",
      "pace":                   "moderate",
      "accessibility_required": false,
      "destination":            "Nairobi",
      "language":               "en",
      "kiosk_id":               "<uuid>|null"
    }

    Response: complete Itinerary with days, attractions, narrative, and QR code.

    This endpoint can take 10–20 seconds (Claude API call).
    Consider showing a loading animation on the kiosk screen.
    """
    user_id = _current_user_uuid()
    try:
        data = _generate_schema.load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    # Save preferences to user_trip_preferences for future personalisation
    _save_trip_preferences(user_id, data)

    try:
        itinerary = itinerary_generator_service.generate(
            user_id=user_id,
            duration_days=data["duration_days"],
            interests=data["interests"],
            budget_level=data["budget_level"],
            pace=data["pace"],
            accessibility_required=data.get("accessibility_required", False),
            destination=data["destination"],
            language=data.get("language", "en"),
            kiosk_id=data.get("kiosk_id"),
        )
    except ValueError as e:
        if "No attractions found matching the given preferences" in str(e):
            return no_result("No itinerary could be generated")
        return bad_request(str(e))
    except RuntimeError as e:
        return bad_request(f"Itinerary generation failed: {e}")

    return created(_serialise_itinerary(itinerary))


# ─── Operator: submit time data ───────────────────────────────────────────────

def submit_operator_time_data(attraction_id: str):
    """
    POST /api/admin/attractions/<attraction_id>/time-data

    Body:
    {
      "avg_minutes":      90,
      "operator_notes":   "Most visitors spend 60–120 minutes here"
    }
    """
    user_id = _current_user_uuid()
    try:
        data = _operator_time_schema.load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    try:
        time_data = attraction_time_data_service.submit_operator_input(
            attraction_id=attraction_id,
            avg_minutes=data["avg_minutes"],
            operator_notes=data.get("operator_notes"),
            submitted_by=user_id,
        )
    except ValueError as e:
        return bad_request(str(e))

    return created({
        "id":           str(time_data.id),
        "attraction_id": str(time_data.attraction_id),
        "avg_minutes":  time_data.avg_minutes,
        "source":       time_data.source.value,
        "confidence":   time_data.confidence,
        "message":      "Visit duration recorded successfully",
    })


# ─── Analytics pipeline: ingest visit duration ───────────────────────────────

def ingest_visit_duration():
    """
    POST /api/internal/analytics/visit-duration
    Called by the analytics event processor (not directly by tourists).

    Body:
    {
      "attraction_id": "<uuid>",
      "checkin_at":    "2024-06-01T09:15:00Z",
      "checkout_at":   "2024-06-01T11:00:00Z"
    }
    """
    try:
        data = _analytics_schema.load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    result = attraction_time_data_service.process_analytics_event_pair(
        attraction_id=data["attraction_id"],
        checkin_at=data["checkin_at"],
        checkout_at=data["checkout_at"],
    )

    if result is None:
        return bad_request("Invalid event pair: checkout must be after check-in")

    return success({
        "attraction_id": str(result.attraction_id),
        "avg_minutes":   result.avg_minutes,
        "sample_count":  result.sample_count,
        "confidence":    round(result.confidence, 3),
    })


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _save_trip_preferences(user_id, data: dict) -> None:
    """
    Persist or update the tourist's trip preferences.
    Used for personalisation in future visits and analytics dashboards.
    """
    from app.models.user_trip_preference import UserTripPreference

    try:
        prefs = UserTripPreference.query.filter_by(user_id=user_id).first()
    except Exception:
        # Remove legacy rows whose user_id was stored with a non-UUID sqlite type.
        db.session.rollback()
        db.session.execute(
            text(
                "DELETE FROM user_trip_preferences "
                "WHERE typeof(user_id) IN ('integer', 'real')"
            )
        )
        db.session.commit()
        prefs = UserTripPreference.query.filter_by(user_id=user_id).first()

    if prefs:
        prefs.trip_duration  = data["duration_days"]
        prefs.budget_level   = data["budget_level"]
        prefs.interests      = ",".join(data["interests"])
        prefs.pace           = data["pace"]
        db.session.commit()
    else:
        db.session.add(UserTripPreference(
            user_id=user_id,
            trip_duration=data["duration_days"],
            budget_level=data["budget_level"],
            interests=",".join(data["interests"]),
            pace=data["pace"],
        ))
        db.session.commit()


def _serialise_itinerary(itinerary) -> dict:
    """
    Serialise a fully loaded Itinerary ORM object into the API response dict.
    Includes days, their attractions, and the QR code URL.
    """
    from app.models.itinerary_day import ItineraryDay
    from app.models.itinerary_day_attraction import ItineraryDayAttraction

    days_out = []
    for day in sorted(itinerary.days, key=lambda d: d.day_number):
        stops = (
            ItineraryDayAttraction.query
            .filter_by(itinerary_day_id=day.id)
            .order_by(ItineraryDayAttraction.visit_order)
            .all()
        )
        days_out.append({
            "day_number":  day.day_number,
            "day_title":   day.title,
            "narrative":   day.narrative,
            "attractions": [s.to_dict() for s in stops],
        })

    return {
        "id":          str(itinerary.id),
        "title":       itinerary.title,
        "status":      itinerary.status.value,
        "qr_code_url": itinerary.qr_code_url,
        "days":        days_out,
        "created_at":  itinerary.created_at.isoformat(),
    }
