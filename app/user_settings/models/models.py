import uuid
from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True) # Keeping original Integer PK
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    accessibility = db.relationship('UserAccessibility', backref='user', uselist=False)
    notifications = db.relationship('UserNotification', backref='user', uselist=False)
    preferences = db.relationship('UserPreference', backref='user', uselist=False)
    embeddings = db.relationship('UserBehaviorEmbedding', backref='user', uselist=False)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Original fields
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    # Client fields
    language_preference = db.Column(db.String(10), default='en')
    currency_preference = db.Column(db.String(3), default='KES')
    timezone = db.Column(db.String(50), default='Africa/Nairobi')
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserAccessibility(db.Model):
    __tablename__ = 'user_accessibility'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Original fields
    accessibility_preference = db.Column(db.String(50))
    font_size = db.Column(db.Integer, default=14)
    # Client fields
    voice_navigation = db.Column(db.Boolean, default=False)
    text_to_speech = db.Column(db.Boolean, default=False)
    large_text = db.Column(db.Boolean, default=False)
    wheelchair_mode = db.Column(db.Boolean, default=False)
    other_needs = db.Column(db.JSON, default={})
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserNotification(db.Model):
    __tablename__ = 'user_notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Original fields/Client overlap
    language_preference = db.Column(db.String(10), default='en')
    email_alerts = db.Column(db.Boolean, default=True) # Mapped to email_enabled
    push_notifications = db.Column(db.Boolean, default=True) # Mapped to push_enabled
    # Client fields
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stay_duration_days = db.Column(db.Integer)
    budget_level = db.Column(db.String(20))
    pace = db.Column(db.String(20))
    interests = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserBehaviorEmbedding(db.Model):
    __tablename__ = 'user_behavior_embeddings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    embedding = db.Column(db.PickleType)
    embedding_model = db.Column(db.String(100))
    embedding_version = db.Column(db.Integer)
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    token = db.Column(db.String, unique=True, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
