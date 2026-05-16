"""
Marshmallow schemas for the itinerary generator and time-data endpoints.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
from marshmallow_enum import EnumField


VALID_INTERESTS = [
    "museum", "heritage_site", "national_park", "wildlife", "beach",
    "cultural", "restaurant", "shopping", "viewpoint", "adventure",
    "gastronomy", "health_wellness", "ecotourism", "birdwatching",
]

VALID_BUDGET_LEVELS = ["low", "medium", "high"]
VALID_PACE_VALUES   = ["relaxed", "moderate", "intensive"]


class GenerateItinerarySchema(Schema):
    """
    Validates POST /api/itineraries/generate

    All fields have sensible defaults so a kiosk can submit a minimal body
    and still get a valid itinerary (e.g. walk-up tourist with no account).
    """
    duration_days = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=30),
        metadata={"example": 5},
    )

    interests = fields.List(
        fields.Str(validate=validate.OneOf(VALID_INTERESTS)),
        required=True,
        validate=validate.Length(min=1, max=8),
        metadata={"example": ["wildlife", "museum", "cultural"]},
    )

    budget_level = fields.Str(
        load_default="medium",
        validate=validate.OneOf(VALID_BUDGET_LEVELS),
    )

    pace = fields.Str(
        load_default="moderate",
        validate=validate.OneOf(VALID_PACE_VALUES),
    )

    accessibility_required = fields.Bool(load_default=False)

    destination = fields.Str(
        load_default="Nairobi",
        validate=validate.Length(min=2, max=100),
    )

    language = fields.Str(
        load_default="en",
        validate=validate.Length(min=2, max=5),
    )

    kiosk_id = fields.UUID(load_default=None, allow_none=True)

    @validates("interests")
    def validate_interests(self, value):
        if not value:
            raise ValidationError("At least one interest is required")
        unknown = set(value) - set(VALID_INTERESTS)
        if unknown:
            raise ValidationError(
                f"Unknown interest(s): {', '.join(unknown)}. "
                f"Valid options: {', '.join(VALID_INTERESTS)}"
            )


class OperatorTimeDataSchema(Schema):
    """Validates POST /api/admin/attractions/<id>/time-data"""

    avg_minutes = fields.Int(
        required=True,
        validate=validate.Range(min=5, max=1440),
        metadata={"example": 90},
    )

    operator_notes = fields.Str(
        load_default=None,
        validate=validate.Length(max=500),
        metadata={"example": "Most visitors spend 60–120 minutes exploring the museum."},
    )


class AnalyticsVisitSchema(Schema):
    """Validates POST /api/internal/analytics/visit-duration"""

    attraction_id = fields.UUID(required=True)
    checkin_at    = fields.DateTime(required=True)
    checkout_at   = fields.DateTime(required=True)
