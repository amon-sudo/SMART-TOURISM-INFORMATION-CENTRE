import os
import uuid
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR

# PostGIS geography is gated by USE_POSTGIS so installs without the
# extension fall back to two float columns rather than crashing on import.
_USE_POSTGIS = os.getenv("USE_POSTGIS", "false").strip().lower() in {"1", "true", "yes", "on"}
if _USE_POSTGIS:
    try:
        from geoalchemy2 import Geography
        _LOCATION_TYPE = Geography(geometry_type="POINT", srid=4326)
        HAS_POSTGIS = True
    except Exception:  # pragma: no cover - dev fallback
        _LOCATION_TYPE = None
        HAS_POSTGIS = False
else:
    _LOCATION_TYPE = None
    HAS_POSTGIS = False


class Attraction(db.Model):
    __tablename__ = "attractions"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    destination_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("destinations.id"),
        nullable=False
    )

    # FK to business_profiles is enforced when the column has a real value.
    # The relationship is one-sided to avoid mandating a back_populates on
    # BusinessProfile, matching the existing kiosk-module pattern.
    business_owner_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("business_profiles.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )

    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)

    category = db.Column(db.String)

    amenities = db.relationship(
    "Amenity",
    secondary="attraction_amenities",
    backref="attractions"
)

    time_data = db.relationship(
        "AttractionTimeData",
        back_populates="attraction",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    
    
    destination = db.relationship(
    "app.tourism_amenitties.destination.models.destination.Destination",
    backref="attractions"
)
    
    # Location for geo-search. PostGIS geography when available, else two
    # floats so the column is always queryable.
    if HAS_POSTGIS and _LOCATION_TYPE is not None:
        location = db.Column(_LOCATION_TYPE, nullable=True)
    else:
        latitude = db.Column(db.Float, nullable=True)
        longitude = db.Column(db.Float, nullable=True)

    avg_rating = db.Column(db.Float, default=0)

    status = db.Column(db.String)

    is_wheelchair_accessible = db.Column(db.Boolean, default=False)

    entry_fee = db.Column(db.Float)

    view_count = db.Column(db.Integer, default=0)

    search_vector = db.Column(TSVECTOR)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    __table_args__ = (
        db.Index("ix_attractions_search_vector", "search_vector", postgresql_using="gin"),
        db.Index("ix_attractions_destination_category_status",
                 "destination_id", "category", "status"),
    )