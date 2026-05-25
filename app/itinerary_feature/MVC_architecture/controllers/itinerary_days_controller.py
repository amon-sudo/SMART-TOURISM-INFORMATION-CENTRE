"""
Itinerary Days Controller
Handles manual day/attraction management for custom (non-AI) itineraries.
"""
from __future__ import annotations

import uuid
from datetime import time as dt_time

from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from marshmallow import Schema, fields, validate, ValidationError, post_load

from app.extensions import db
from app.models.itinerary import Itinerary, ItineraryStatus
from app.models.itinerary_day import ItineraryDay
from app.itinerary_feature.MVC_architecture.models.itinerary_day_attraction import (
    ItineraryDayAttraction,
)
from app.utils.api_response import success, created, bad_request
from flask import abort


# ── Schemas ───────────────────────────────────────────────────────────────────

class DayCreateSchema(Schema):
    day_number = fields.Int(required=True, validate=validate.Range(min=1))
    title = fields.Str(load_default=None, validate=validate.Length(max=255))
    narrative = fields.Str(load_default=None)


class DayUpdateSchema(Schema):
    title = fields.Str(load_default=None, validate=validate.Length(max=255))
    narrative = fields.Str(load_default=None)


class DayAttractionAddSchema(Schema):
    attraction_id = fields.UUID(required=True)
    visit_order = fields.Int(load_default=1, validate=validate.Range(min=1))
    start_time = fields.Str(load_default="09:00")
    duration_minutes = fields.Int(load_default=60, validate=validate.Range(min=1))
    narrative_note = fields.Str(load_default=None)


def _day_to_dict(day: ItineraryDay) -> dict:
    return {
        "id": str(day.id),
        "itinerary_id": str(day.itinerary_id),
        "day_number": day.day_number,
        "title": day.title,
        "narrative": day.narrative,
        "attractions": [a.to_dict() for a in (day.day_attractions or [])],
    }


def _current_user_uuid():
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
    except Exception:
        identity = None
    if identity in (None, "", "None"):
        identity = request.headers.get("X-User-Id")
    if identity in (None, "", "None"):
        abort(401, description="Authentication required")
    if isinstance(identity, uuid.UUID):
        return identity
    return uuid.UUID(str(identity))


def _get_itinerary(itinerary_id: str, user_id: uuid.UUID) -> Itinerary:
    it = Itinerary.query.filter_by(id=itinerary_id, user_id=user_id).first_or_404(
        description="Itinerary not found"
    )
    if it.status == ItineraryStatus.ARCHIVED:
        abort(400, description="Cannot edit an archived itinerary")
    return it


# ── Controllers ───────────────────────────────────────────────────────────────

def add_day(itinerary_id: str):
    """POST /api/v1/itineraries/<id>/days"""
    user_id = _current_user_uuid()
    it = _get_itinerary(itinerary_id, user_id)

    try:
        data = DayCreateSchema().load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    day = ItineraryDay(
        itinerary_id=it.id,
        day_number=data["day_number"],
        title=data.get("title"),
        narrative=data.get("narrative"),
    )
    db.session.add(day)
    db.session.commit()
    return created(_day_to_dict(day))


def update_day(itinerary_id: str, day_id: str):
    """PATCH /api/v1/itineraries/<id>/days/<day_id>"""
    user_id = _current_user_uuid()
    _get_itinerary(itinerary_id, user_id)

    day = ItineraryDay.query.filter_by(id=day_id, itinerary_id=itinerary_id).first_or_404(
        description="Day not found"
    )

    try:
        data = DayUpdateSchema().load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    if data.get("title") is not None:
        day.title = data["title"]
    if data.get("narrative") is not None:
        day.narrative = data["narrative"]

    db.session.commit()
    return success(_day_to_dict(day))


def remove_day(itinerary_id: str, day_id: str):
    """DELETE /api/v1/itineraries/<id>/days/<day_id>"""
    user_id = _current_user_uuid()
    _get_itinerary(itinerary_id, user_id)

    day = ItineraryDay.query.filter_by(id=day_id, itinerary_id=itinerary_id).first_or_404(
        description="Day not found"
    )
    db.session.delete(day)
    db.session.commit()
    return success({"message": "Day removed"})


def add_attraction_to_day(itinerary_id: str, day_id: str):
    """POST /api/v1/itineraries/<id>/days/<day_id>/attractions"""
    user_id = _current_user_uuid()
    _get_itinerary(itinerary_id, user_id)

    day = ItineraryDay.query.filter_by(id=day_id, itinerary_id=itinerary_id).first_or_404(
        description="Day not found"
    )

    try:
        data = DayAttractionAddSchema().load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    # Parse start_time string "HH:MM" → time object
    try:
        h, m = str(data["start_time"]).split(":")
        parsed_time = dt_time(int(h), int(m))
    except Exception:
        parsed_time = dt_time(9, 0)

    entry = ItineraryDayAttraction(
        itinerary_day_id=day.id,
        attraction_id=data["attraction_id"],
        visit_order=data["visit_order"],
        start_time=parsed_time,
        duration_minutes=data["duration_minutes"],
        narrative_note=data.get("narrative_note"),
    )
    db.session.add(entry)
    db.session.commit()
    db.session.refresh(entry)
    return created(entry.to_dict())


def remove_attraction_from_day(itinerary_id: str, day_id: str, entry_id: str):
    """DELETE /api/v1/itineraries/<id>/days/<day_id>/attractions/<entry_id>"""
    user_id = _current_user_uuid()
    _get_itinerary(itinerary_id, user_id)

    entry = ItineraryDayAttraction.query.filter_by(
        id=entry_id, itinerary_day_id=day_id
    ).first_or_404(description="Attraction entry not found")

    db.session.delete(entry)
    db.session.commit()
    return success({"message": "Attraction removed from day"})
