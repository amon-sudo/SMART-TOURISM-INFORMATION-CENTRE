from marshmallow import Schema, fields, validate


class PermissionCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    description = fields.String(load_default=None)
    module = fields.String(load_default=None)
    action = fields.String(load_default=None)
    scope = fields.String(load_default=None)


class PermissionResponseSchema(Schema):
    id = fields.String()
    name = fields.String()
    description = fields.String()
    module = fields.String()
    action = fields.String()
    scope = fields.String()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()