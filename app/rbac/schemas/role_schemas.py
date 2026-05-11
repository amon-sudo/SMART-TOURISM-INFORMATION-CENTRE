from marshmallow import Schema, fields, validate


class RoleCreateSchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=50)
    )
    description = fields.String(load_default=None)
    is_active = fields.Boolean(load_default=True)


class RoleResponseSchema(Schema):
    id = fields.Integer()
    uuid = fields.String()
    name = fields.String()
    description = fields.String()
    is_active = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()