
import uuid
from datetime import datetime, timezone

from app.extensions import db


class BusinessRegistrationRequest(db.Model):
    __tablename__ = "business_registration_requests"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_name = db.Column(db.String(255), nullable=False)
    business_type = db.Column(db.String(50), nullable=False)
    registration_doc = db.Column(db.String(512), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    reviewed_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    business_profile_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("business_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
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

    business_profile = db.relationship("BusinessProfile", foreign_keys=[business_profile_id], lazy="select")

   