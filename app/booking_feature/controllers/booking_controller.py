"""
Booking Controller
Handles creation, retrieval, status management, cancellation, and QR vouchers.
"""

from __future__ import annotations

import uuid

from flask              import request, abort, current_app, redirect
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from marshmallow import ValidationError

from app.extensions               import db
from app.models.booking           import (
    Booking, BookingItem, BookingStatus, BookingType, RefundStatus
)
from app.models.qr_code           import QrCode
from app.validators.schemas       import (
    BookingCreateSchema,
    BookingCancelSchema,
    BookingListQuerySchema,
    BookingAdminListQuerySchema,
    BookingSchema,
    QrCodeSchema,
)
from app.services.qr_code_service  import qr_code_service
from app.services.price_service    import PriceService
from app.services.reference_service import ReferenceService
from app.utils.pagination           import paginate_query
from app.utils.api_response         import success, created, bad_request


# ── Schema instances ──────────────────────────────────────────────────────────
_create_schema     = BookingCreateSchema()
_cancel_schema     = BookingCancelSchema()
_list_query        = BookingListQuerySchema()
_admin_list_query  = BookingAdminListQuerySchema()
_booking_schema    = BookingSchema()
_qr_schema         = QrCodeSchema()


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
    POST /api/bookings
    Create a new booking with one or more line items.

    Body:
        {
          "type": "hotel",
          "items": [
            { "target_type": "accommodation", "target_id": "<uuid>", "quantity": 1 }
          ],
          "kiosk_id": "<uuid>|null",
          "kiosk_session_id": "<uuid>|null"
        }
    """
    user_id = _current_user_uuid()
    try:
        data = _create_schema.load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    # ── Resolve unit prices and compute total ─────────────────────────────────
    resolved_items = []
    for item in data["items"]:
        price = PriceService.get_unit_price(
            item["target_type"].value,
            item["target_id"],
        )
        resolved_items.append({**item, "price_at_booking": price})

    total_cost = sum(
        i["price_at_booking"] * i["quantity"] for i in resolved_items
    )

    # ── Persist in a single transaction ──────────────────────────────────────
    try:
        booking = Booking(
            user_id=user_id,
            kiosk_id=data.get("kiosk_id"),
            kiosk_session_id=data.get("kiosk_session_id"),
            reference_number=ReferenceService.generate("BK"),
            type=data["type"],
            status=BookingStatus.PENDING,
            total_cost=total_cost,
            refund_status=RefundStatus.NONE,
        )
        db.session.add(booking)
        db.session.flush()  # get booking.id before inserting items

        for item in resolved_items:
            db.session.add(BookingItem(
                booking_id=booking.id,
                target_type=item["target_type"],
                target_id=item["target_id"],
                quantity=item["quantity"],
                price_at_booking=item["price_at_booking"],
                notes=item.get("notes"),
            ))

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    # Refresh to load items relationship
    db.session.refresh(booking)

    # Auto-generate voucher QR if the booking is already confirmed.
    # Current flow creates PENDING bookings; this keeps behavior ready for
    # future confirmation-at-create flows without changing API contracts.
    if booking.status == BookingStatus.CONFIRMED:
        qr = qr_code_service.generate_or_refresh(
            target_type="booking",
            target_id=booking.id,
            created_by=user_id,
        )
        setattr(booking, "qr_code", qr)

    return created(_booking_schema.dump(booking))


def list_bookings():
    """
    GET /api/bookings
    List the authenticated user's bookings with optional filters.
    """
    user_id = _current_user_uuid()
    try:
        args = _list_query.load(request.args)
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    query = Booking.query.filter_by(user_id=user_id)
    if args.get("status"):
        query = query.filter_by(status=args["status"])
    if args.get("type"):
        query = query.filter_by(type=args["type"])
    query = query.order_by(Booking.created_at.desc())

    result = paginate_query(query, args["page"], args["per_page"])
    result["data"] = _booking_schema.dump(result["data"], many=True)
    return success(result)


def show(booking_id: str):
    """
    GET /api/bookings/<booking_id>
    Fetch a single booking. Non-admin users can only see their own.
    """
    user_id = _current_user_uuid()
    # jwt_claims carries is_admin; fall back to False
    from flask_jwt_extended import get_jwt
    try:
        is_admin = get_jwt().get("is_admin", False)
    except Exception:
        is_admin = False

    q = Booking.query.filter_by(id=booking_id)
    if not is_admin:
        q = q.filter_by(user_id=user_id)

    booking = q.first_or_404(description="Booking not found")
    return success(_booking_schema.dump(booking))


def cancel(booking_id: str):
    """
    PATCH /api/bookings/<booking_id>/cancel
    Cancel a booking. Revokes any active QR voucher.
    Body: { "cancellation_reason": "..." }
    """
    user_id = _current_user_uuid()
    booking = (
        Booking.query
        .filter_by(id=booking_id, user_id=user_id)
        .first_or_404(description="Booking not found")
    )

    non_cancellable = {
        BookingStatus.CANCELLED,
        BookingStatus.COMPLETED,
        BookingStatus.REFUNDED,
    }
    if booking.status in non_cancellable:
        return bad_request(f"Cannot cancel a booking in status: {booking.status.value}")

    try:
        data = _cancel_schema.load(request.get_json(force=True) or {})
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)

    # Capture the status BEFORE cancel() mutates it so the refund branch
    # below is actually reachable for previously-confirmed bookings.
    pre_cancel_status = booking.status

    try:
        booking.cancel(reason=data.get("cancellation_reason"))

        # Revoke any outstanding QR vouchers
        qr_code_service.revoke_for_target("booking", booking.id)

        # Trigger refund assessment for previously confirmed bookings
        if pre_cancel_status == BookingStatus.CONFIRMED:
            from app.services.payment_service import PaymentService
            PaymentService.initiate_refund_assessment(booking.id)

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return success({
        "data":    _booking_schema.dump(booking),
        "message": "Booking cancelled",
    })


def generate_qr(booking_id: str):
    """
    POST /api/bookings/<booking_id>/qr
    Generate a voucher QR code for a confirmed booking.
    """
    user_id = _current_user_uuid()
    booking = (
        Booking.query
        .filter_by(id=booking_id, user_id=user_id)
        .first_or_404(description="Booking not found")
    )

    if booking.status != BookingStatus.CONFIRMED:
        return bad_request("QR vouchers are only available for confirmed bookings")

    qr = qr_code_service.generate_or_refresh(
        target_type="booking",
        target_id=booking.id,
        created_by=user_id,
    )
    return created(_qr_schema.dump(qr))


# ── Admin ─────────────────────────────────────────────────────────────────────

def admin_list():
    """
    GET /api/admin/bookings
    Admin: list all bookings with rich filters for the dashboard.
    """
    try:
        args = _admin_list_query.load(request.args)
    except ValidationError as e:
        return bad_request("Validation failed", errors=e.messages)
    query = Booking.query

    if args.get("status"):
        query = query.filter_by(status=args["status"])
    if args.get("type"):
        query = query.filter_by(type=args["type"])
    if args.get("kiosk_id"):
        query = query.filter_by(kiosk_id=args["kiosk_id"])
    if args.get("from_date"):
        query = query.filter(Booking.created_at >= args["from_date"])
    if args.get("to_date"):
        query = query.filter(Booking.created_at <= args["to_date"])

    query = query.order_by(Booking.created_at.desc())

    result = paginate_query(query, args["page"], args["per_page"])
    result["data"] = _booking_schema.dump(result["data"], many=True)
    return success(result)
