from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from app.authanduser.models.models import User, PasswordReset

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        exclude = ("password_hash",)  # 🔹 don’t expose password hash

    id = fields.UUID(dump_only=True)
    email = fields.Email(required=True)
    username = fields.String(required=False)   # 🔹 NEW FIELD
    created_at = fields.DateTime(dump_only=True)

class PasswordResetSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PasswordReset
        load_instance = True
        include_fk = True

    token = fields.String()
    expires_at = fields.DateTime()
    used_at = fields.DateTime(allow_none=True)
