"""New models needed for P4 endpoints."""

import uuid
from datetime import datetime

from app.extensions import db


class Favourite(db.Model):
    """STORY044 — tourists save attractions to a favourites list."""

    __tablename__ = "favourites"
    __table_args__ = (
        db.UniqueConstraint("user_id", "attraction_id", name="uq_favourites_user_attraction"),
        db.Index("ix_favourites_user", "user_id"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Polymorphic-friendly: not a hard FK so favouriting other entity types
    # (events, tour packages) later is a column addition rather than a new
    # table. For now everything is an attraction.
    attraction_id = db.Column(db.Uuid(as_uuid=True), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "attraction_id": str(self.attraction_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    """STORY039 — in-app notification log + read state."""

    __tablename__ = "notifications"
    __table_args__ = (
        db.Index("ix_notifications_user_unread", "user_id", "is_read"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type = db.Column(db.String(50), nullable=False)  # booking_confirmed, itinerary_reminder, ...
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=True)
    channel = db.Column(db.String(20), default="in_app", nullable=False)  # in_app|email|push|sms
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "type": self.type,
            "title": self.title,
            "body": self.body,
            "channel": self.channel,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }
