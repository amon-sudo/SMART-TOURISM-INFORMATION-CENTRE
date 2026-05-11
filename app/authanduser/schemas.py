from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from app.authanduser.models.models import User, PasswordReset

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        exclude = ("password_hash",)  # 🔹 FIX: don’t expose password hash

class PasswordResetSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PasswordReset
        load_instance = True
        include_fk = True

    token = fields.String()
    expires_at = fields.DateTime()
    used = fields.Boolean()
