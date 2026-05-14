import uuid
from datetime import datetime
from app.extensions import db
from app.utils.base_model import BaseUUIDModel
from app.rbac.models.user_role import UserRole

class User(BaseUUIDModel):
    __tablename__ = 'users'
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    accessibility = db.relationship('UserAccessibility', backref='user', uselist=False)
    notifications = db.relationship('UserNotification', backref='user', uselist=False)
    preferences = db.relationship('UserPreference', backref='user', uselist=False)
    embeddings = db.relationship('UserBehaviorEmbedding', backref='user', uselist=False)
    business_profile = db.relationship('BusinessProfile', back_populates='user', uselist=False)
    
    # Auth Relationships
    refresh_tokens = db.relationship("RefreshToken", backref="user", lazy=True)
    password_resets = db.relationship("PasswordReset", backref="user", lazy=True)
    roles = db.relationship("UserRole", backref="user", lazy=True, cascade="all, delete-orphan", foreign_keys="[UserRole.user_id]")


class RefreshToken(BaseUUIDModel):
    __tablename__ = "refresh_tokens"
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(512), nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class PasswordReset(BaseUUIDModel):
    __tablename__ = "password_resets"
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(512), nullable=False)
    used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
