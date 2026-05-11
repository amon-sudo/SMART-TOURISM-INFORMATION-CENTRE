"""
Business Profile Model
========================
The public-facing profile of a verified business on the platform.
A BusinessProfile record is created automatically when an admin approves a
BusinessRegistrationRequest.  Until that approval the business cannot submit
listings or appear in public-facing API responses.

Relationships (outbound):
    - user                  : The owning business-owner account (users.id)
    - registration_request  : The originating approval record (one-to-one)
    - media_gallery         : Primary logo / gallery images (polymorphic)
    - attractions           : Listings submitted by this business
"""

import uuid
from datetime import datetime, timezone
from app.extensions import db


# ---------------------------------------------------------------------------
# Enumerations kept as module-level constants so they can be imported by
# Marshmallow schemas and service-layer validators without importing the ORM
# model (avoids circular-import issues in large projects).
# ---------------------------------------------------------------------------

BUSINESS_TYPE_ENUM = (
    "hotel",
    "restaurant",
    "tour_operator",
    "transport",
    "attraction",
    "other",
)


class BusinessProfile(db.Model):
    __tablename__ = "business_profiles"

    id = db.Column(db.UUID(as_uuid=True),primary_key=True,default=uuid.uuid4,nullable=False,)
    user_id = db.Column(db.UUID(as_uuid=True),db.ForeignKey("users.id", ondelete="CASCADE"),nullable=False,unique=True,index=True,comment="FK → users.id  (the business owner)",)
    registration_request_id = db.Column(db.UUID(as_uuid=True),db.ForeignKey("business_registration_requests.id", ondelete="SET NULL"),nullable=True,unique=True, comment="FK → business_registration_requests.id",)
    business_name = db.Column(db.String(255),nullable=False,
                              comment="Trading / brand name displayed to tourists",)
    business_type = db.Column(db.String(50),nullable=False,comment=(
            "Category of business. "
            "Enum: hotel | restaurant | tour_operator | transport | attraction | other"
        ),
    )
    phone = db.Column(db.String(30),nullable=True,
        comment="Public contact phone number (E.164 recommended)",
    )
    email = db.Column(db.String(255),nullable=True,
        comment="Public contact email (may differ from login email)",
    )
    address = db.Column(db.Text,nullable=True,
        comment="Physical / postal address shown on the profile page",
    )
   
  
    description = db.Column(db.Text,nullable=True,
        comment="Public description of the business and its offerings",
    )
    media_gallery_id = db.Column(db.UUID(as_uuid=True),db.ForeignKey("media_gallery.id", ondelete="SET NULL"),nullable=True,
        comment="FK → media_gallery.id  (primary logo record)",
    )
    verified = db.Column(db.Boolean,nullable=False,default=False,index=True,
        comment=(
            "True once the registration request is approved and "
            "the business is allowed to publish listings."
        ),
    )
    is_active = db.Column(db.Boolean,nullable=False,default=True,index=True,
        comment="False if the profile has been suspended or soft-deleted",
    )
    created_at = db.Column(db.DateTime(timezone=True),nullable=False,default=lambda: datetime.now(timezone.utc),
        comment="When this profile was created (i.e. when request was approved)",
    )
    updated_at = db.Column(db.DateTime(timezone=True),nullable=False,default=lambda: datetime.now(timezone.utc),onupdate=lambda: datetime.now(timezone.utc),
        comment="Last modification timestamp (auto-managed)",
    )
 #relationships
    user = db.relationship("User",foreign_keys=[user_id],back_populates="business_profile",lazy="select",)
    registration_request = db.relationship("BusinessRegistrationRequest",back_populates="business_profile",foreign_keys=[registration_request_id],lazy="select",)
    primary_media = db.relationship("MediaGallery",foreign_keys=[media_gallery_id],lazy="select",)
# All attractions submitted by this business owner.
    attractions = db.relationship("Attraction",foreign_keys="Attraction.business_owner_id",back_populates="business_owner",lazy="dynamic",cascade="all, delete-orphan",)

 