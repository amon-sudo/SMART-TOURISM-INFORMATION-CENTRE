import uuid
from datetime import datetime
from app.extensions import db
from app.utils.base_model import BaseUUIDModel

from app.authanduser.models.models import User, RefreshToken, PasswordReset

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    language_preference = db.Column(db.String(10), default='en')
    currency_preference = db.Column(db.String(3), default='KES')
    timezone = db.Column(db.String(50), default='Africa/Nairobi')
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserAccessibility(db.Model):
    __tablename__ = 'user_accessibility'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    accessibility_preference = db.Column(db.String(50)) # e.g., 'Screen Reader', 'High Contrast'
    font_size = db.Column(db.Integer, default=14)
    voice_navigation = db.Column(db.Boolean, default=False)
    text_to_speech = db.Column(db.Boolean, default=False)
    large_text = db.Column(db.Boolean, default=False)
    wheelchair_mode = db.Column(db.Boolean, default=False)
    other_needs = db.Column(db.JSON, default={})
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserNotification(db.Model):
    __tablename__ = 'user_notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    language_preference = db.Column(db.String(10), default='en')
    email_alerts = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    email_enabled = db.Column(db.Boolean, default=True)
    push_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=False)
    marketing_emails_enabled = db.Column(db.Boolean, default=False)
    security_alerts_enabled = db.Column(db.Boolean, default=True)
    booking_updates_enabled = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    stay_duration_days = db.Column(db.Integer)
    budget_level = db.Column(db.String(20))
    pace = db.Column(db.String(20))
    interests = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserBehaviorEmbedding(db.Model):
    __tablename__ = 'user_behavior_embeddings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    embedding = db.Column(db.PickleType)
    embedding_model = db.Column(db.String(100))
    embedding_version = db.Column(db.Integer)
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

