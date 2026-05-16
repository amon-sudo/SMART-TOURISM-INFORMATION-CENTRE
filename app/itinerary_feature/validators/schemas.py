"""
Marshmallow schemas for Itinerary, Booking, BookingItem, and QrCode.
Used for:
  - request body validation (load)
  - response serialisation  (dump)
"""

from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from marshmallow_enum import EnumField

from app.models.itinerary import ItineraryStatus
from app.models.booking   import BookingType, BookingStatus, RefundStatus, BookingItemTargetType
from app.models.qr_code   import QrCodeStatus, QrTargetType


# ─── QrCode ───────────────────────────────────────────────────────────────────

class QrCodeSchema(Schema):
    id          = fields.UUID(dump_only=True)
    target_type = EnumField(QrTargetType,   by_value=True, dump_only=True)
    target_id   = fields.UUID(dump_only=True)
    url         = fields.Url(dump_only=True)
    image_path  = fields.Str(dump_only=True, allow_none=True)
    token       = fields.Str(dump_only=True)
    scan_count  = fields.Int(dump_only=True)
    expires_at  = fields.DateTime(dump_only=True, allow_none=True)
    status      = EnumField(QrCodeStatus, by_value=True, dump_only=True)
    created_by  = fields.UUID(dump_only=True, allow_none=True)
    created_at  = fields.DateTime(dump_only=True)
    updated_at  = fields.DateTime(dump_only=True)


class QrCodeListQuerySchema(Schema):
    """Query-string schema for GET /admin/qr-codes."""
    target_type = EnumField(QrTargetType, by_value=True, load_default=None)
    status      = EnumField(QrCodeStatus, by_value=True, load_default=None)
    target_id   = fields.UUID(load_default=None)
    page        = fields.Int(load_default=1,  validate=validate.Range(min=1))
    per_page    = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))


# ─── Itinerary ────────────────────────────────────────────────────────────────

class ItineraryCreateSchema(Schema):
    """Validates POST /api/itineraries body."""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=255),
        metadata={"example": "5-Day Wildlife & Culture Tour"},
    )


class ItineraryUpdateSchema(Schema):
    """Validates PATCH /api/itineraries/<id> body."""
    title = fields.Str(
        load_default=None,
        validate=validate.Length(min=3, max=255),
    )


class ItinerarySchema(Schema):
    """Full serialisation for API responses."""
    id          = fields.UUID(dump_only=True)
    user_id     = fields.UUID(dump_only=True)
    title       = fields.Str()
    status      = EnumField(ItineraryStatus, by_value=True)
    qr_code_url = fields.Str(allow_none=True)
    created_at  = fields.DateTime(dump_only=True)
    updated_at  = fields.DateTime(dump_only=True)
    # Nested
    qr_code     = fields.Nested(QrCodeSchema, dump_only=True, allow_none=True)


class ItineraryListQuerySchema(Schema):
    status   = EnumField(ItineraryStatus, by_value=True, load_default=None)
    page     = fields.Int(load_default=1,  validate=validate.Range(min=1))
    per_page = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))


# ─── BookingItem ──────────────────────────────────────────────────────────────

class BookingItemInputSchema(Schema):
    """Inline within BookingCreateSchema.items[]."""
    target_type = EnumField(
        BookingItemTargetType,
        by_value=True,
        required=True,
    )
    target_id   = fields.UUID(required=True)
    quantity    = fields.Int(
        required=True,
        validate=validate.Range(min=1),
    )
    notes       = fields.Str(
        load_default=None,
        validate=validate.Length(max=500),
    )


class BookingItemSchema(Schema):
    """Full serialisation of a booking line item."""
    id               = fields.UUID(dump_only=True)
    booking_id       = fields.UUID(dump_only=True)
    target_type      = EnumField(BookingItemTargetType, by_value=True)
    target_id        = fields.UUID()
    quantity         = fields.Int()
    price_at_booking = fields.Float()
    subtotal         = fields.Float(dump_only=True)
    notes            = fields.Str(allow_none=True)


# ─── Booking ──────────────────────────────────────────────────────────────────

class BookingCreateSchema(Schema):
    """Validates POST /api/bookings body."""
    type             = EnumField(BookingType, by_value=True, required=True)
    items            = fields.List(
        fields.Nested(BookingItemInputSchema),
        required=True,
        validate=validate.Length(min=1),
    )
    kiosk_id         = fields.UUID(load_default=None, allow_none=True)
    kiosk_session_id = fields.UUID(load_default=None, allow_none=True)

    @validates("items")
    def validate_items(self, items, **kwargs):
        if not items:
            raise ValidationError("items must contain at least one entry")
        return items


class BookingCancelSchema(Schema):
    """Validates PATCH /api/bookings/<id>/cancel body."""
    cancellation_reason = fields.Str(
        load_default=None,
        validate=validate.Length(max=500),
    )


class BookingSchema(Schema):
    """Full serialisation for API responses."""
    id                  = fields.UUID(dump_only=True)
    user_id             = fields.UUID(dump_only=True)
    kiosk_id            = fields.UUID(dump_only=True, allow_none=True)
    kiosk_session_id    = fields.UUID(dump_only=True, allow_none=True)
    reference_number    = fields.Str(dump_only=True)
    type                = EnumField(BookingType,   by_value=True)
    status              = EnumField(BookingStatus, by_value=True)
    total_cost          = fields.Float()
    cancelled_at        = fields.DateTime(dump_only=True, allow_none=True)
    cancellation_reason = fields.Str(dump_only=True, allow_none=True)
    refund_status       = EnumField(RefundStatus,  by_value=True)
    created_at          = fields.DateTime(dump_only=True)
    updated_at          = fields.DateTime(dump_only=True)
    # Nested
    items               = fields.List(fields.Nested(BookingItemSchema), dump_only=True)
    qr_code             = fields.Nested(QrCodeSchema, dump_only=True, allow_none=True)


class BookingListQuerySchema(Schema):
    status   = EnumField(BookingStatus, by_value=True, load_default=None)
    type     = EnumField(BookingType,   by_value=True, load_default=None)
    page     = fields.Int(load_default=1,  validate=validate.Range(min=1))
    per_page = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))


class BookingAdminListQuerySchema(Schema):
    status    = EnumField(BookingStatus, by_value=True, load_default=None)
    type      = EnumField(BookingType,   by_value=True, load_default=None)
    kiosk_id  = fields.UUID(load_default=None)
    from_date = fields.DateTime(load_default=None)
    to_date   = fields.DateTime(load_default=None)
    page      = fields.Int(load_default=1,  validate=validate.Range(min=1))
    per_page  = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))


# ─── Shared pagination wrapper ────────────────────────────────────────────────

class PaginatedResponseSchema(Schema):
    """Wraps any list response with pagination metadata."""
    data        = fields.List(fields.Raw())
    total       = fields.Int()
    page        = fields.Int()
    per_page    = fields.Int()
    total_pages = fields.Int()
