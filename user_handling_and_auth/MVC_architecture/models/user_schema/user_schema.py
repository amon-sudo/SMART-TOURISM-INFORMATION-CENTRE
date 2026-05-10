from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    id = fields.Integer(dump_only=True)
    username = fields.String(required=True, validate=validate.Length(min=3, max=30))
    email = fields.Email(required=True)
    password = fields.String(load_only=True, required=True, validate=validate.Length(min=8))
    is_active = fields.Boolean(load_default=True)
    deleted_at = fields.DateTime(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    roles = fields.Method("get_roles", dump_only=True)

    def get_roles(self, obj):
        user_roles = getattr(obj, "roles", None)
        if not user_roles:
            return []
        return [ur.role.name for ur in user_roles if getattr(ur, "role", None)]
        