import uuid
from datetime import datetime
from app.extensions import db

class BaseUUIDModel(db.Model):
    """Base model that uses UUID for primary keys and includes timestamps."""
    __abstract__ = True

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
