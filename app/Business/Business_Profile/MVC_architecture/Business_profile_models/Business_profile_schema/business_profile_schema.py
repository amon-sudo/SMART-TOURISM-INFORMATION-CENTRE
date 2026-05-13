from marshmallow import Schema, fields, validate


BUSINESS_TYPE_ENUM = ("hotel", "restaurant", "tour_operator", "transport", "attraction", "other")

BUSINESS_TYPE_VALIDATOR = validate.OneOf(
    BUSINESS_TYPE_ENUM,
    error="business_type must be one of: " + ", ".join(BUSINESS_TYPE_ENUM),
)

business_type_validator = validate.OneOf(
    BUSINESS_TYPE_ENUM,
    error="Invalid business type."
)


class BusinessProfileSchema(Schema):
    """Base schema – all profile fields."""
    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    registration_request_id = fields.UUID(dump_only=True)
    business_name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    business_type = fields.String(validate=business_type_validator)
    media_url = fields.UUID(dump_only=True)
    verified = fields.Boolean(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class BusinessProfileUpdateSchema(Schema):
    """Schema for PATCH requests – all fields optional."""
    business_name = fields.String(validate=validate.Length(min=2, max=255))
    business_type = fields.String(validate=business_type_validator)
    media_url = fields.UUID(dump_only=True)
    address = fields.String()
    description = fields.String()


class BusinessProfileResponseSchema(BusinessProfileSchema):
    """Schema for public-facing profile responses."""
    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    registration_request_id = fields.UUID(dump_only=True)
    business_name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    business_type = fields.String(validate=business_type_validator)
    media_url = fields.UUID(dump_only=True)
    verified = fields.Boolean(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class BusinessProfileAdminResponseSchema(BusinessProfileSchema):
    """Schema for admin-facing profile responses (includes extra fields)."""
    user_id = fields.UUID(dump_only=True)
    registration_request_id = fields.UUID(dump_only=True)
    is_active = fields.Boolean()
    verified = fields.Boolean()