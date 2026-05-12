from marshmallow import Schema, fields, validate


class RoleCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=50))
    description = fields.String(load_default=None)
    is_system = fields.Boolean(load_default=False)


class RoleResponseSchema(Schema):
    id = fields.String()
    name = fields.String()
    description = fields.String()
    is_system = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()