import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    module = db.Column(db.String(50), nullable=True)
    action = db.Column(db.String(30), nullable=True)
    scope = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    roles = db.relationship("RolePermission", back_populates="permission", lazy="dynamic")

    def __repr__(self):
        return f"<Permission {self.name}>"