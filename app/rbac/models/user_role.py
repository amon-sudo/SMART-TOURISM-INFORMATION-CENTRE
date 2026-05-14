from datetime import datetime
from app.extensions import db


class UserRole(db.Model):
    __tablename__ = "user_roles"

    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id"), primary_key=True, nullable=False)
    role_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("roles.id"), primary_key=True, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id"), nullable=True)

    role = db.relationship("Role", back_populates="users")

    def __repr__(self):
        return f"<UserRole user={self.user_id} role={self.role_id}>"
