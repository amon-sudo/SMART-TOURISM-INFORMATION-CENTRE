from app.extensions import db
from app.utils.responses import ApiResponse
from ..models import (
    User, UserProfile, UserAccessibility, UserNotification, 
    UserPreference, UserBehaviorEmbedding
)
from ..schemas import (
    UserProfileSchema, UserAccessibilitySchema, UserNotificationSchema, 
    UserPreferenceSchema, UserBehaviorEmbeddingSchema
)
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        return ApiResponse.success(data={
            "profile": profile_schema.dump(profile) if profile else {},
            "accessibility": accessibility_schema.dump(accessibility) if accessibility else {},
            "notifications": notification_schema.dump(notifications) if notifications else {},
            "preferences": preference_schema.dump(preferences) if preferences else {}
        })
    except Exception as e:
        logger.error(f"Error fetching settings for user {user_id}: {str(e)}")
        return ApiResponse.error(message="An internal error occurred while fetching settings.")

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
        
        # Check if user exists
        if not db.session.get(User, user_id):
            return ApiResponse.error(message=f"User with ID {user_id} not found.", status_code=404)
            
        record = model_class.query.filter_by(user_id=user_id).first()
        
        if record:
            for key, value in validated_data.items():
                setattr(record, key, value)
        else:
            validated_data['user_id'] = user_id
            record = model_class(**validated_data)
            db.session.add(record)
            
        db.session.commit()
        return ApiResponse.success(
            data=schema.dump(record),
            message=f"{label} updated successfully"
        )

    except ValidationError as err:
        return ApiResponse.error(message="Validation failed", code="VALIDATION_ERROR", details=err.messages, status_code=400)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating {label} for user {user_id}: {str(e)}")
        return ApiResponse.error(message="Database transaction failed.", code="DB_ERROR")
    except Exception as e:
        logger.error(f"Unexpected error updating {label} for user {user_id}: {str(e)}")
        return ApiResponse.error(message="An unexpected error occurred.")
