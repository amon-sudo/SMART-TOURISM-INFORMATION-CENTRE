"""
Marshmallow schemas for Itinerary, Booking, BookingItem, and QrCode.
Used for:
  - request body validation (load)
  - response serialisation  (dump)
"""

from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from marshmallow_enum import EnumField

from app.qr_code.MVC_architecture.models.qr_code import QrCodeStatus, QrTargetType
# Note: Itinerary and Booking imports commented out - these models are in separate modules
# from app.itinerary_feature.models import ItineraryStatus
# from app.booking_feature.models import BookingType, BookingStatus, RefundStatus, BookingItemTargetType


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


# ───────────────────────────────────────────────────────────────────────────
# NOTE: Itinerary, Booking, and other schemas have been moved to their
#       respective feature modules (itinerary_feature, booking_feature, etc.)
#       to avoid circular imports and maintain module isolation.
# ───────────────────────────────────────────────────────────────────────────
