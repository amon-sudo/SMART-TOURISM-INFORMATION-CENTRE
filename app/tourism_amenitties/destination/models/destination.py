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

    slug = db.Column(db.String, unique=True, nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )