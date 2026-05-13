from importlib.metadata import metadata

from marshmallow import Schema, ValidationError, fields, pre_load, validate, validates_schema


BUSINESS_TYPE_CHOICES = (
    "hotel",
    "restaurant",
    "tour_operator",
    "transport",
    "attraction",
    "other",
)

BUSINESS_TYPE_VALIDATOR = validate.OneOf(
    BUSINESS_TYPE_CHOICES,
    error="Invalid business type.",
)

REGISTRATION_STATUS_CHOICES = ("pending", "approved", "rejected", "suspended")

REGISTRATION_STATUS_VALIDATOR = validate.OneOf(
    REGISTRATION_STATUS_CHOICES,
    error="status must be one of: pending, approved, rejected, suspended",
)


class BusinessRegistrationRequestCreateSchema(Schema):
    """Schema for creating a business registration request."""

    business_name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    business_type = fields.Str(required=True, validate=BUSINESS_TYPE_VALIDATOR)
    registration_doc = fields.Dict(
        keys=fields.Str(),
        values=fields.Raw(),
        required=False,
        load_default=dict,
        metadata={
            "description": (
                "Optional JSONB bag for uploaded doc URLs "
                "(e.g. registration_certificate_url, tax_pin)"
            )
        },
    )

    @pre_load
    def strip_whitespace(self, data: dict, **kwargs) -> dict:
        for field in ("business_name", "business_type", "registration_doc"):
            value = data.get(field)
            if isinstance(value, str):
                data[field] = value.strip()
        return data


class BusinessRegistrationRequestUpdateSchema(Schema):
    """Schema for updating applicant-managed registration fields."""

    business_name = fields.Str(validate=validate.Length(min=2, max=255))
    business_type = fields.Str(validate=BUSINESS_TYPE_VALIDATOR)
    registration_doc = fields.Dict(
        keys=fields.Str(), values=fields.Raw(), allow_none=True
    )
    @validates_schema
    def validate_non_empty_payload(self, data: dict, **kwargs) -> None:
        if not data:
            raise ValidationError("Provide at least one field to update.")


class BusinessRegistrationRequestAdminActionSchema(Schema):
    """Schema for admin actions on registration requests."""

    status = fields.Str(required=True, validate=REGISTRATION_STATUS_VALIDATOR)
    rejection_reason = fields.Str(
        load_default=None,
        validate=validate.Length(max=1000),
        metadata={
            "description": "Mandatory when status is 'rejected' or 'suspended'"
        },
    )
class BusinessRegistrationRequestResponseSchema(Schema):
    """Schema for serializing business registration request records."""

    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    business_name = fields.Str(dump_only=True)
    business_type = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    rejection_reason = fields.Str(allow_none=True, dump_only=True)
    reviewed_by = fields.UUID(allow_none=True, dump_only=True)
    reviewed_at = fields.DateTime(allow_none=True, dump_only=True)
    business_profile_id = fields.UUID(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)