from marshmallow import Schema, fields, validate


BUSINESS_TYPE_CHOICES = (
    "hotel", "restaurant", "tour_operator", "transport", "attraction", "other"
)

business_type_validator = validate.OneOf(
    BUSINESS_TYPE_CHOICES,
    error="Invalid business type."
)


class BusinessProfileSchema(Schema):
    """Base schema – all profile fields."""
    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    registration_request_id = fields.UUID(dump_only=True)
    business_name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    business_type = fields.String(required=True, validate=business_type_validator)
    phone = fields.String(validate=validate.Length(max=30))
    email = fields.Email()
    address = fields.String()
    description = fields.String()
    verified = fields.Boolean(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class BusinessProfileUpdateSchema(Schema):
    """Schema for PATCH requests – all fields optional."""
    business_name = fields.String(validate=validate.Length(min=2, max=255))
    business_type = fields.String(validate=business_type_validator)
    phone = fields.String(validate=validate.Length(max=30))
    email = fields.Email()
    address = fields.String()
    description = fields.String()


class BusinessProfileResponseSchema(BusinessProfileSchema):
    """Schema for public-facing profile responses."""
    pass


class BusinessProfileAdminResponseSchema(BusinessProfileSchema):
    """Schema for admin-facing profile responses (includes extra fields)."""
    is_active = fields.Boolean()
    verified = fields.Boolean()
