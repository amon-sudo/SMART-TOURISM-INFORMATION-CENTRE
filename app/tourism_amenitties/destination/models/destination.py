import uuid
from app.extensions import db


class Destination(db.Model):
    __tablename__ = "destinations"
    __table_args__ = {"extend_existing": True}

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    canonical_name = db.Column(db.String, nullable=False)

    name = db.Column(db.String(255), nullable=True, index=True)

    slug = db.Column(db.String, unique=True, nullable=False)

    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    emergency_contacts = db.relationship(
        "EmergencyContact",
        backref="destination",
        cascade="all, delete-orphan"
    )