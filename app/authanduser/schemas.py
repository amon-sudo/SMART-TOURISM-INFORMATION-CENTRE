# app/authanduser/schemas.py
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from app.authanduser.models import User, RefreshToken, PasswordReset

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True

    id = fields.UUID(dump_only=True)
    email = fields.Email(required=True)
    password_hash = fields.String(load_only=True)   # never expose on output
    created_at = fields.DateTime(dump_only=True)


class RefreshTokenSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RefreshToken
        load_instance = True
        include_fk = True

    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(required=True)
    token = fields.String(required=True)
    revoked = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    expires_at = fields.DateTime(required=True)


class PasswordResetSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PasswordReset
        load_instance = True
        include_fk = True

    id = fields.UUID(dump_only=True)
    user_id = fields.UUID(required=True)
    token = fields.String(required=True)
    used = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    expires_at = fields.DateTime(required=True)
