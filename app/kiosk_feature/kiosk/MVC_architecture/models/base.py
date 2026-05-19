"""
Base model mixin.
Provides id (UUID PK), created_at, updated_at, and convenience helpers
that every model inherits.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy                      import Column, DateTime
from sqlalchemy.ext.declarative      import declared_attr

from app.extensions import db


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Adds created_at / updated_at columns with automatic population."""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )


class UUIDPrimaryKeyMixin:
    """UUID v4 primary key, generated server-side by Python (no DB extension needed)."""

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class BaseModel(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """
    Abstract base class for all models.
    Subclass this instead of db.Model directly.

    Usage:
        class Itinerary(BaseModel):
            __tablename__ = 'itineraries'
            ...
    """

    __abstract__ = True

    def save(self) -> "BaseModel":
        """Persist this instance (add + commit)."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> None:
        """Delete this instance (remove + commit)."""
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs) -> "BaseModel":
        """Update arbitrary columns and commit."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    def to_dict(self) -> dict:
        """Shallow dict representation of all mapped columns."""
        result = {}
        for col in self.__table__.columns:
            value = getattr(self, col.name)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[col.name] = value
        return result

    @classmethod
    def get_by_id(cls, record_id) -> "BaseModel | None":
        return cls.query.get(record_id)

    @classmethod
    def get_or_404(cls, record_id) -> "BaseModel":
        from flask import abort
        instance = cls.query.get(record_id)
        if instance is None:
            abort(404, description=f"{cls.__name__} not found")
        return instance
