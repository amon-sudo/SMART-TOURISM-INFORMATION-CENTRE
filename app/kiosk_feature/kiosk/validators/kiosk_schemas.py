"""
Marshmallow schemas for all kiosk endpoints.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
from marshmallow_enum import EnumField

from app.models.kiosk import KioskStatus, KioskLocationType
from app.models.kiosk_support_models import HealthEventType, MaintenanceType


CONTENT_TYPES = [
    "attractions", "events", "emergency_contacts",
    "transport", "accommodations", "maps",
]


# ── Kiosk device ──────────────────────────────────────────────────────────────

class KioskCreateSchema(Schema):
    name          = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    location_type = EnumField(KioskLocationType, by_value=True, required=True)
    address       = fields.Str(load_default=None, validate=validate.Length(max=500))
    business_profile_id = fields.UUID(load_default=None, allow_none=True)
    lat           = fields.Float(load_default=None, allow_none=True,
                                 validate=validate.Range(min=-90, max=90))
    lng           = fields.Float(load_default=None, allow_none=True,
                                 validate=validate.Range(min=-180, max=180))
    configuration = fields.Dict(load_default={})

    @validates("lat")
    def validate_lat_lng_pair(self, lat):
        # Both or neither
        pass  # cross-field validation handled in controller if needed


class KioskUpdateSchema(Schema):
    name          = fields.Str(load_default=None, validate=validate.Length(min=3, max=255))
    address       = fields.Str(load_default=None, validate=validate.Length(max=500))
    location_type = EnumField(KioskLocationType, by_value=True, load_default=None)
    status        = EnumField(KioskStatus,        by_value=True, load_default=None)
    configuration = fields.Dict(load_default=None)


class KioskListQuerySchema(Schema):
    status        = EnumField(KioskStatus,        by_value=True, load_default=None)
    location_type = EnumField(KioskLocationType,  by_value=True, load_default=None)
    page          = fields.Int(load_default=1,  validate=validate.Range(min=1))
    per_page      = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))


# ── Heartbeat & health ────────────────────────────────────────────────────────

class MetricsSchema(Schema):
    cpu_percent        = fields.Float(load_default=None)
    ram_percent        = fields.Float(load_default=None)
    disk_percent       = fields.Float(load_default=None)
    uptime_seconds     = fields.Int(load_default=None)
    network_latency_ms = fields.Int(load_default=None)
    app_version        = fields.Str(load_default=None)
    screen_brightness  = fields.Int(load_default=None)


class HeartbeatSchema(Schema):
    metrics = fields.Nested(MetricsSchema, load_default={})


class HealthEventSchema(Schema):
    event_type    = EnumField(HealthEventType, by_value=True, required=True)
    metrics       = fields.Nested(MetricsSchema, load_default=None)
    error_message = fields.Str(load_default=None, validate=validate.Length(max=1000))


# ── Content sync ──────────────────────────────────────────────────────────────

class ContentSyncSchema(Schema):
    content_type = fields.Str(
        required=True,
        validate=validate.OneOf(CONTENT_TYPES),
    )
    payload = fields.List(
        fields.Dict(),
        required=True,
        validate=validate.Length(min=0),
    )


# ── Session ───────────────────────────────────────────────────────────────────

class SessionStartSchema(Schema):
    user_id     = fields.UUID(load_default=None, allow_none=True)
    device_info = fields.Dict(load_default={})


class SessionStateUpdateSchema(Schema):
    """
    Accepts any subset of the session state to merge in.
    Common keys: step, language, destination, duration_days,
                 interests, budget_level, pace, itinerary_draft
    """
    state_patch = fields.Dict(
        required=True,
        metadata={"description": "Key-value pairs to merge into session state"},
    )

    @validates("state_patch")
    def validate_patch(self, value):
        if not value:
            raise ValidationError("state_patch must not be empty")


class SessionAnalyticsQuerySchema(Schema):
    from_date = fields.DateTime(load_default=None)
    to_date   = fields.DateTime(load_default=None)


# ── Maintenance ───────────────────────────────────────────────────────────────

class MaintenanceLogSchema(Schema):
    maintenance_type = EnumField(MaintenanceType, by_value=True, required=True)
    notes            = fields.Str(load_default=None, validate=validate.Length(max=1000))
    duration_minutes = fields.Int(load_default=None, validate=validate.Range(min=1))
    details          = fields.Dict(load_default=None)
