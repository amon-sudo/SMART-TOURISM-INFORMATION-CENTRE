import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
# from geoalchemy2 import Geography


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

    business_owner_id = db.Column(
        UUID(as_uuid=True),
        # db.ForeignKey("business_profiles.id"),
        nullable=False
    )

    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)

    category = db.Column(db.String)

    amenities = db.relationship(
    "Amenity",
    secondary="attraction_amenities",
    backref="attractions"
)
    
    
    destination = db.relationship(
    "Destination",
    backref="attractions"
)
    
    # PostGIS geography column
    # location = db.Column(Geography(geometry_type="POINT", srid=4326))

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