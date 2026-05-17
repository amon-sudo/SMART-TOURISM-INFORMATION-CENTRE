import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class RolePermission(db.Model):
    __tablename__ = "role_permissions"

    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey("roles.id"), primary_key=True, nullable=False)
    permission_id = db.Column(UUID(as_uuid=True), db.ForeignKey("permissions.id"), primary_key=True, nullable=False)

    role = db.relationship("Role", back_populates="permissions")
    permission = db.relationship("Permission", back_populates="roles")

    def __repr__(self):
        return f"<RolePermission role={self.role_id} permission={self.permission_id}>"