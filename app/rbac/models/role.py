from datetime import datetime
import uuid
from app.extensions import db


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    permissions = db.relationship("RolePermission", back_populates="role", lazy="dynamic")
    users = db.relationship("UserRole", back_populates="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"