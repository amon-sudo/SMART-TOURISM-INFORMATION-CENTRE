from app.extensions import db
from ..models.models import UserProfile, UserAccessibility, UserNotification
from ..schemas.schemas import UserProfileSchema, UserAccessibilitySchema, UserNotificationSchema

# Initialize schemas
profile_schema = UserProfileSchema()
accessibility_schema = UserAccessibilitySchema()
notification_schema = UserNotificationSchema()

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
