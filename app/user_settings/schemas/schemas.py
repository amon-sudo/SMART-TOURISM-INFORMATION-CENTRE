from marshmallow import Schema, fields

class UserProfileSchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(required=True)
    full_name = fields.String()
    bio = fields.String()
    profile_picture = fields.String()
    language_preference = fields.String()
    currency_preference = fields.String()
    timezone = fields.String()
    last_login_at = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class UserAccessibilitySchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(required=True)
    accessibility_preference = fields.String()
    font_size = fields.Integer()
    voice_navigation = fields.Boolean()
    text_to_speech = fields.Boolean()
    large_text = fields.Boolean()
    wheelchair_mode = fields.Boolean()
    other_needs = fields.Dict()
    updated_at = fields.DateTime(dump_only=True)

class UserNotificationSchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(required=True)
    language_preference = fields.String()
    email_alerts = fields.Boolean()
    push_notifications = fields.Boolean()
    email_enabled = fields.Boolean()
    push_enabled = fields.Boolean()
    sms_enabled = fields.Boolean()
    marketing_emails_enabled = fields.Boolean()
    security_alerts_enabled = fields.Boolean()
    booking_updates_enabled = fields.Boolean()
    updated_at = fields.DateTime(dump_only=True)

class UserPreferenceSchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(required=True)
    stay_duration_days = fields.Integer()
    budget_level = fields.String()
    pace = fields.String()
    interests = fields.Dict()
    updated_at = fields.DateTime(dump_only=True)

class UserBehaviorEmbeddingSchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(required=True)
    embedding_model = fields.String()
    embedding_version = fields.Integer()
    last_updated_at = fields.DateTime(dump_only=True)
from app.extensions import ma
from ..models.models import UserProfile, UserAccessibility, UserNotification
from marshmallow import fields

class UserProfileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserProfile
        load_instance = True
        include_fk = True

class UserAccessibilitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserAccessibility
        load_instance = True
        include_fk = True
        exclude = ('accessibility_preference',)
    # Alias for frontend friendliness
    preference = fields.String(attribute='accessibility_preference')

class UserNotificationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserNotification
        load_instance = True
        include_fk = True
        exclude = ('language_preference',)
    # Alias for frontend friendliness
    language = fields.String(attribute='language_preference')
