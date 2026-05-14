from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.extensions import db


class BusinessProfile(db.Model):
    __tablename__ = "business_profiles"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    registration_request_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("business_registration_requests.id"), nullable=True, unique=True)
    business_type = db.Column(db.String(50), nullable=True)
    business_name = db.Column(db.String(255), nullable=True)
    # media_url = db.Column(db.UUID(as_uuid=True), db.ForeignKey("media.id", ondelete="SET NULL"), nullable=True)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    #relationships
    user = db.relationship("User", back_populates="business_profile", uselist=False)
    registration_request = db.relationship("BusinessRegistrationRequest", back_populates="business_profile", uselist=False)
    media = db.relationship("Media", back_populates="business_profile", uselist=False)
    attractions = db.relationship("Attraction", back_populates="business_profile", lazy="dynamic", cascade="all, delete-orphan")