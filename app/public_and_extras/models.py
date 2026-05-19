"""New models needed for P4 endpoints + ERD completeness."""

import uuid
from datetime import datetime, date

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


class AnalyticsEvent(db.Model):
    """Global analytics event stream (ERD: analytics_events).

    Separate from kiosk_analytics_events so we can record anonymous web/
    mobile activity that isn't tied to a kiosk session.
    """

    __tablename__ = "analytics_events"
    __table_args__ = (
        db.Index("ix_analytics_events_user_created", "user_id", "created_at"),
        db.Index("ix_analytics_events_event_type", "event_type"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    kiosk_id = db.Column(db.Uuid(as_uuid=True), nullable=True)
    event_metadata = db.Column("metadata", db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "user_id": str(self.user_id) if self.user_id else None,
            "kiosk_id": str(self.kiosk_id) if self.kiosk_id else None,
            "metadata": self.event_metadata,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserActivity(db.Model):
    """User activity log (ERD: user_activities).

    Generic "user did X to Y" record — captures favourite/unfavourite,
    review submission, profile updates, booking views, etc.
    """

    __tablename__ = "user_activities"
    __table_args__ = (
        db.Index("ix_user_activities_user_created", "user_id", "created_at"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type = db.Column(db.String(80), nullable=False)
    target_type = db.Column(db.String(60), nullable=True)
    target_id = db.Column(db.Uuid(as_uuid=True), nullable=True)
    activity_metadata = db.Column("metadata", db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "activity_type": self.activity_type,
            "target_type": self.target_type,
            "target_id": str(self.target_id) if self.target_id else None,
            "metadata": self.activity_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DailyAnalyticsSnapshot(db.Model):
    """Pre-computed daily roll-up powering the admin analytics dashboard.

    Re-computed nightly (or on demand) so the dashboard doesn't have to
    aggregate raw analytics_events on every request.
    """

    __tablename__ = "daily_analytics_snapshots"
    __table_args__ = (
        db.UniqueConstraint("date", name="uq_daily_analytics_date"),
    )

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    total_sessions = db.Column(db.Integer, default=0, nullable=False)
    total_bookings = db.Column(db.Integer, default=0, nullable=False)
    total_users_active = db.Column(db.Integer, default=0, nullable=False)
    popular_attraction_id = db.Column(db.Uuid(as_uuid=True), nullable=True)
    avg_session_duration_seconds = db.Column(db.Float, default=0.0, nullable=False)
    avg_rating = db.Column(db.Float, default=0.0, nullable=False)
    booking_conversion_rate = db.Column(db.Float, default=0.0, nullable=False)
    top_searches = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "date": self.date.isoformat() if self.date else None,
            "total_sessions": self.total_sessions,
            "total_bookings": self.total_bookings,
            "total_users_active": self.total_users_active,
            "popular_attraction_id": str(self.popular_attraction_id) if self.popular_attraction_id else None,
            "avg_session_duration_seconds": self.avg_session_duration_seconds,
            "avg_rating": self.avg_rating,
            "booking_conversion_rate": self.booking_conversion_rate,
            "top_searches": self.top_searches,
        }
