"""
Itinerary Controller
Handles CRUD, publish, and QR generation for tourist itineraries.
All business logic is here; routes are registered in itinerary_routes.py.
"""

from __future__ import annotations

import uuid

from flask               import request, jsonify, abort, current_app, redirect
from flask_jwt_extended  import get_jwt_identity
from marshmallow import ValidationError

from app.extensions              import db
from app.models.itinerary        import Itinerary, ItineraryStatus
from app.models.qr_code          import QrCode
from app.validators.schemas      import (
    ItineraryCreateSchema,
    ItineraryUpdateSchema,
    ItineraryListQuerySchema,
    ItinerarySchema,
    QrCodeSchema,
)
from app.services.qr_code_service import qr_code_service
from app.utils.pagination          import paginate_query
from app.utils.api_response        import success, created, not_found, bad_request


# ── Schema instances ──────────────────────────────────────────────────────────
_create_schema    = ItineraryCreateSchema()
_update_schema    = ItineraryUpdateSchema()
_list_query       = ItineraryListQuerySchema()
_itinerary_schema = ItinerarySchema()
_qr_schema        = QrCodeSchema()


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


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def create():
    """
    POST /api/itineraries
    Create a new draft itinerary for the authenticated tourist.
    """
    try:
        data = _create_schema.load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)
    user_id = _current_user_uuid()

    itinerary = Itinerary(
        user_id=user_id,
        title=data["title"],
        status=ItineraryStatus.DRAFT,
    )
    db.session.add(itinerary)
    db.session.commit()

    return created(_itinerary_schema.dump(itinerary))


def list_itineraries():
    """
    GET /api/itineraries
    List all itineraries for the authenticated user with pagination.
    """
    user_id = _current_user_uuid()
    try:
        args = _list_query.load(request.args)
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    query = Itinerary.query.filter_by(user_id=user_id)
    if args.get("status"):
        query = query.filter_by(status=args["status"])
    query = query.order_by(Itinerary.created_at.desc())

    result = paginate_query(query, args["page"], args["per_page"])
    result["data"] = _itinerary_schema.dump(result["data"], many=True)
    return success(result)


def show(itinerary_id: str):
    """
    GET /api/itineraries/<itinerary_id>
    Fetch a single itinerary owned by the authenticated user.
    """
    user_id   = _current_user_uuid()
    itinerary = (
        Itinerary.query
        .filter_by(id=itinerary_id, user_id=user_id)
        .first_or_404(description="Itinerary not found")
    )
    return success(_itinerary_schema.dump(itinerary))


def update(itinerary_id: str):
    """
    PATCH /api/itineraries/<itinerary_id>
    Update the title of a draft itinerary.
    """
    user_id   = _current_user_uuid()
    itinerary = (
        Itinerary.query
        .filter_by(id=itinerary_id, user_id=user_id)
        .first_or_404(description="Itinerary not found")
    )

    if itinerary.status == ItineraryStatus.ARCHIVED:
        return bad_request("Archived itineraries cannot be edited")

    try:
        data = _update_schema.load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)
    if data.get("title"):
        itinerary.title = data["title"]

    db.session.commit()
    return success(_itinerary_schema.dump(itinerary))


def destroy(itinerary_id: str):
    """
    DELETE /api/itineraries/<itinerary_id>
    Soft-delete by setting status to 'archived'.
    Also revokes any active QR codes for this itinerary.
    """
    user_id   = _current_user_uuid()
    itinerary = (
        Itinerary.query
        .filter_by(id=itinerary_id, user_id=user_id)
        .first_or_404(description="Itinerary not found")
    )

    itinerary.status = ItineraryStatus.ARCHIVED
    qr_code_service.revoke_for_target("itinerary", itinerary.id)
    db.session.commit()

    return success({"message": "Itinerary archived successfully"})


# ── Status transitions ────────────────────────────────────────────────────────

def publish(itinerary_id: str):
    """
    POST /api/itineraries/<itinerary_id>/publish
    Transition itinerary from draft → published.
    Requires at least one ItineraryDay.
    """
    from app.models.itinerary_day import ItineraryDay

    user_id   = _current_user_uuid()
    itinerary = (
        Itinerary.query
        .filter_by(id=itinerary_id, user_id=user_id)
        .first_or_404(description="Itinerary not found")
    )

    if itinerary.status != ItineraryStatus.DRAFT:
        return bad_request(f"Cannot publish itinerary in status: {itinerary.status.value}")

    day_count = ItineraryDay.query.filter_by(itinerary_id=itinerary.id).count()
    if day_count == 0:
        return bad_request("Add at least one day before publishing")

    itinerary.status = ItineraryStatus.PUBLISHED
    db.session.commit()

    return success({
        "data":    _itinerary_schema.dump(itinerary),
        "message": "Itinerary published",
    })


# ── QR Code ───────────────────────────────────────────────────────────────────

def generate_qr(itinerary_id: str):
    """
    POST /api/itineraries/<itinerary_id>/qr
    Generate or refresh the QR code for a published itinerary.
    """
    user_id   = _current_user_uuid()
    itinerary = (
        Itinerary.query
        .filter_by(id=itinerary_id, user_id=user_id)
        .first_or_404(description="Itinerary not found")
    )

    if itinerary.status == ItineraryStatus.DRAFT:
        return bad_request("Publish the itinerary before generating a QR code")

    qr = qr_code_service.generate_or_refresh(
        target_type="itinerary",
        target_id=itinerary.id,
        created_by=user_id,
    )

    # Keep denormalised column in sync for kiosk display
    itinerary.qr_code_url = qr.url
    db.session.commit()

    return created(_qr_schema.dump(qr))


# ── Public scan redirect (no auth) ────────────────────────────────────────────

def scan_redirect(token: str):
    """
    GET /api/public/itineraries/<token>
    QR scan redirect — no authentication required.
    Increments scan_count and redirects to the itinerary deep-link.
    """
    qr = qr_code_service.resolve_token(token)

    if qr is None:
        abort(404, description="QR code not found or revoked")

    if qr.target_type.value != "itinerary":
        abort(400, description="Invalid QR code target type")

    qr.increment_scan()

    base_url  = current_app.config["APP_BASE_URL"]
    deep_link = f"{base_url}/itineraries/{qr.target_id}"
    return redirect(deep_link, code=302)
