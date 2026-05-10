from app.extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    accessibility = db.relationship('UserAccessibility', backref='user', uselist=False)
    notifications = db.relationship('UserNotification', backref='user', uselist=False)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))

class UserAccessibility(db.Model):
    __tablename__ = 'user_accessibility'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    accessibility_preference = db.Column(db.String(50)) # e.g., 'Screen Reader', 'High Contrast'
    font_size = db.Column(db.Integer, default=14)

class UserNotification(db.Model):
    __tablename__ = 'user_notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    language_preference = db.Column(db.String(10), default='en')
    email_alerts = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
