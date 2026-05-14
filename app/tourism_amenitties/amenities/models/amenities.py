import uuid
from app.extensions import db


class Amenity(db.Model):
    __tablename__ = "amenities"

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = db.Column(db.String, nullable=False)

    icon_url = db.Column(db.String)