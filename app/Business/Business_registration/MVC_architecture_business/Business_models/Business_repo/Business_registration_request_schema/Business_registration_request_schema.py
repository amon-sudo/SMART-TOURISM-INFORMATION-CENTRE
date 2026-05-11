
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load

from ...Business_domain.Business_registration_request_domain.Business_registration_request_domain import BusinessRegistrationRequest

Business_type_validator = validate.OneOf(
    ["hotel", "restaurant", "tour_operator", "transport", "attraction", "other"],
    error="Invalid business type. Must be one of: hotel, restaurant, tour_operator, transport, attraction, other."
)

registration_status_validator = validate.OneOf(
    ["pending", "approved", "rejected", "suspended"],
    error="Invalid registration status. Must be one of: pending, approved, rejected, suspended."
)


class BusinessRegistrationRequestSchema(Schema):
    """Base schema aligned with business_registration_requests table."""
    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(dump_only=True)
    business_name = fields.String(required=True, validate=validate.Length(min=3, max=255))
    business_type = fields.String(required=True, validate=Business_type_validator)
    registration_doc = fields.String(required=True, validate=validate.Length(min=3, max=512))
    status = fields.String(dump_only=True, validate=registration_status_validator)
    reviewed_by = fields.UUID(dump_only=True, load_default=None)
    reviewed_at = fields.DateTime(dump_only=True)
    business_profile_id = fields.UUID(dump_only=True, load_default=None)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class BusinessRegistrationRequestCreateSchema(BusinessRegistrationRequestSchema):
    """Schema for creating a new registration request (all required fields enforced)."""

    @post_load
    def make_registration_request(self, data, **kwargs):
        return data  # Return plain dict; service layer creates the model instance.


class BusinessRegistrationRequestUpdateSchema(Schema):
    """Schema for partially updating a rejected request before resubmission."""
    business_name = fields.String(validate=validate.Length(min=3, max=255))
    business_type = fields.String(validate=Business_type_validator)
    registration_doc = fields.String(validate=validate.Length(min=3, max=512))


class BusinessRegistrationRequestAdminActionSchema(Schema):
    """Schema for an admin approve/reject/suspend action."""
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            ["approved", "rejected", "suspended"],
            error="status must be one of: approved, rejected, suspended."
        ),
    )
    business_profile_id = fields.UUID(load_default=None)


class BusinessRegistrationRequestResponseSchema(BusinessRegistrationRequestSchema):
    """Schema used to serialise a registration request in API responses."""
    pass

