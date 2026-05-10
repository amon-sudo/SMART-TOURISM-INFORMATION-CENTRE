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
