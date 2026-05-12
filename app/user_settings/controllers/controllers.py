from app.extensions import db
from ..models.models import (
    UserProfile, UserAccessibility, UserNotification, 
    UserPreference, UserBehaviorEmbedding
)
from ..schemas.schemas import (
    UserProfileSchema, UserAccessibilitySchema, UserNotificationSchema, 
    UserPreferenceSchema, UserBehaviorEmbeddingSchema
)
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from ..models.models import UserProfile, UserAccessibility, UserNotification
from ..schemas.schemas import UserProfileSchema, UserAccessibilitySchema, UserNotificationSchema

# Initialize schemas
profile_schema = UserProfileSchema()
accessibility_schema = UserAccessibilitySchema()
notification_schema = UserNotificationSchema()
preference_schema = UserPreferenceSchema()
embedding_schema = UserBehaviorEmbeddingSchema()

def get_all_settings(user_id):
    """Retrieve all user-related settings."""
    try:
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        accessibility = UserAccessibility.query.filter_by(user_id=user_id).first()
        notifications = UserNotification.query.filter_by(user_id=user_id).first()
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        return {
            "status": "success",
            "data": {
                "profile": profile_schema.dump(profile) if profile else {},
                "accessibility": accessibility_schema.dump(accessibility) if accessibility else {},
                "notifications": notification_schema.dump(notifications) if notifications else {},
                "preferences": preference_schema.dump(preferences) if preferences else {}
            }
        }, 200
    except Exception as e:
        logger.error(f"Error fetching settings for user {user_id}: {str(e)}")
        return {"status": "error", "message": "An internal error occurred while fetching settings."}, 500

def update_user_profile(user_id, data):
    return _update_setting_generic(user_id, data, UserProfile, profile_schema, "Profile")

def update_accessibility_settings(user_id, data):
    return _update_setting_generic(user_id, data, UserAccessibility, accessibility_schema, "Accessibility settings")

def update_notification_settings(user_id, data):
    return _update_setting_generic(user_id, data, UserNotification, notification_schema, "Notification settings")

def update_user_preferences(user_id, data):
    return _update_setting_generic(user_id, data, UserPreference, preference_schema, "Preferences")

def _update_setting_generic(user_id, data, model_class, schema, label):
    """Generic helper to update or create a setting record."""
    try:
        validated_data = schema.load(data, partial=True)
        record = model_class.query.filter_by(user_id=user_id).first()
        
        if record:
            for key, value in validated_data.items():
                setattr(record, key, value)
        else:
            validated_data['user_id'] = user_id
            record = model_class(**validated_data)
            db.session.add(record)
            
        db.session.commit()
        return {
            "status": "success", 
            "message": f"{label} updated successfully",
            "data": schema.dump(record)
        }, 200

    except ValidationError as err:
        return {"status": "error", "message": "Validation failed", "errors": err.messages}, 400
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating {label} for user {user_id}: {str(e)}")
        return {"status": "error", "message": "Database transaction failed."}, 500
    except Exception as e:
        logger.error(f"Unexpected error updating {label} for user {user_id}: {str(e)}")
        return {"status": "error", "message": "An unexpected error occurred."}, 500

def get_settings(user_id):
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    accessibility = UserAccessibility.query.filter_by(user_id=user_id).first()
    notifications = UserNotification.query.filter_by(user_id=user_id).first()
    
    return {
        "profile": profile_schema.dump(profile) if profile else {},
        "accessibility": accessibility_schema.dump(accessibility) if accessibility else {},
        "notifications": notification_schema.dump(notifications) if notifications else {}
    }

from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

def update_settings(user_id, data):
    try:
        # Update Profile
        if 'profile' in data:
            p = UserProfile.query.filter_by(user_id=user_id).first()
            if p: p = profile_schema.load(data['profile'], instance=p, partial=True)
            else: p = profile_schema.load({**data['profile'], 'user_id': user_id})
            db.session.add(p)

        # Update Accessibility
        if 'accessibility' in data:
            if 'preference' in data['accessibility']:
                data['accessibility']['accessibility_preference'] = data['accessibility'].pop('preference')
            a = UserAccessibility.query.filter_by(user_id=user_id).first()
            if a: a = accessibility_schema.load(data['accessibility'], instance=a, partial=True)
            else: a = accessibility_schema.load({**data['accessibility'], 'user_id': user_id})
            db.session.add(a)

        # Update Notifications
        if 'notifications' in data:
            if 'language' in data['notifications']:
                data['notifications']['language_preference'] = data['notifications'].pop('language')
            n = UserNotification.query.filter_by(user_id=user_id).first()
            if n: n = notification_schema.load(data['notifications'], instance=n, partial=True)
            else: n = notification_schema.load({**data['notifications'], 'user_id': user_id})
            db.session.add(n)

        db.session.commit()
        return {"message": "Settings updated successfully"}, 200

    except ValidationError as err:
        return {"message": "Validation failed", "errors": err.messages}, 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return {"message": "Database error", "error": str(e)}, 500
