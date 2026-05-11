from datetime import datetime
from app.extensions import db
from app.user_handling_and_auth.utilities.password_hashing.password_hashing import hash_password, verify_password
from app.models.user_role import UserRole


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to user-role assignments.
    roles = db.relationship(
        'UserRole',
        primaryjoin='User.id == foreign(UserRole.user_id)',
        backref='user',
        lazy=True,
    )

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(password, self.password_hash)