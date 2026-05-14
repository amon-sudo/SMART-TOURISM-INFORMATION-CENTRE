import uuid
from datetime import datetime

from sqlalchemy import Index, UniqueConstraint
from app.extensions import db

# Use PostgreSQL UUID when available; otherwise fall back to a 36-char string
try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    UUID_TYPE = PG_UUID(as_uuid=True)
except Exception:
    UUID_TYPE = db.String(36)

# Try to import Geography from geoalchemy2; fallback to Text if unavailable
try:
    from geoalchemy2 import Geography
    GEOGRAPHY_AVAILABLE = True
except Exception:
    Geography = None
    GEOGRAPHY_AVAILABLE = False

# -------------------------
# User model
# -------------------------
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.email}>"

# -------------------------
# Destination model
# -------------------------
class Destination(db.Model):
    __tablename__ = "destinations"

    id = db.Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Destination {self.name} ({self.id})>"

# -------------------------
# Feedback / Media models
# -------------------------
class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tourist_id = db.Column(UUID_TYPE, db.ForeignKey("users.id"), nullable=False)
    target_type = db.Column(db.String(64), nullable=False)
    target_id = db.Column(UUID_TYPE, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_reviews_target_status", "target_type", "target_id", "status"),
        UniqueConstraint("tourist_id", "target_type", "target_id", name="uq_reviews_tourist_target"),
    )

    def __repr__(self) -> str:
        return f"<Review id={self.id} target={self.target_type}:{self.target_id} tourist={self.tourist_id}>"

class MediaGallery(db.Model):
    __tablename__ = "media_gallery"

    id = db.Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    target_type = db.Column(db.String(64), nullable=False)
    target_id = db.Column(UUID_TYPE, nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    media_type = db.Column(db.String(64), nullable=True)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_media_target", "target_type", "target_id"),
    )

    def __repr__(self) -> str:
        return f"<Media id={self.id} url={self.url} primary={self.is_primary}>"

class EmergencyContact(db.Model):
    __tablename__ = "emergency_contacts"

    id = db.Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    destination_id = db.Column(UUID_TYPE, db.ForeignKey("destinations.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(64), nullable=True)
    street = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    if GEOGRAPHY_AVAILABLE:
        location = db.Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    else:
        location = db.Column(db.Text, nullable=True)

    __table_args__ = (
        Index("idx_contacts_destination", "destination_id"),
    )

    def __repr__(self) -> str:
        return f"<EmergencyContact id={self.id} name={self.name} destination={self.destination_id}>"
