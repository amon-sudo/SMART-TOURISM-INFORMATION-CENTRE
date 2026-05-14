import uuid
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID


class AttractionAmenity(db.Model):
    __tablename__ = "attraction_amenities"

    attraction_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("attractions.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )

    amenity_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("amenities.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )