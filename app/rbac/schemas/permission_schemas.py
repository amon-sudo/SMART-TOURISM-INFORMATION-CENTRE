from marshmallow import Schema, fields, validate


class PermissionCreateSchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100)
    )
    description = fields.String(load_default=None)
    module = fields.String(load_default=None)
    is_active = fields.Boolean(load_default=True)


class PermissionResponseSchema(Schema):
    id = fields.Integer()
    uuid = fields.String()
    name = fields.String()
    description = fields.String()
    module = fields.String()
    is_active = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()