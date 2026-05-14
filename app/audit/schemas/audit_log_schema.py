from marshmallow import Schema, fields, validate


class AuditLogCreateSchema(Schema):
    actor_user_id = fields.String(load_default=None)
    action = fields.String(required=True, validate=validate.Length(min=2, max=100))
    entity_type = fields.String(required=True, validate=validate.Length(min=2, max=100))
    entity_id = fields.String(load_default=None)
    kiosk_id = fields.String(load_default=None)
    old_values = fields.Dict(load_default=None)
    new_values = fields.Dict(load_default=None)
    ip_address = fields.String(load_default=None)
    user_agent = fields.String(load_default=None)
    extra_data = fields.Dict(load_default=dict)


class AuditLogResponseSchema(Schema):
    id = fields.String()
    actor_user_id = fields.String()
    action = fields.String()
    entity_type = fields.String()
    entity_id = fields.String()
    kiosk_id = fields.String()
    old_values = fields.Dict()
    new_values = fields.Dict()
    ip_address = fields.String()
    user_agent = fields.String()
    extra_data = fields.Dict()
    created_at = fields.DateTime()