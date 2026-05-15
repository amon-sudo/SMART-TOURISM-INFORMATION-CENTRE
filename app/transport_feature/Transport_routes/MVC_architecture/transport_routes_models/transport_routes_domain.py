import uuid
from datetime import datetime
from app.extensions import db
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import relationship


class TransportRoute(db.Model):
    __tablename__ = "transport_routes"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = db.Column(String(50), nullable=False)  # e.g., bus, train, tram
    origin_station_id = db.Column(Uuid(as_uuid=True), ForeignKey("stations.id"), nullable=False)
    #destination_station_id = db.Column(UUID(as_uuid=True), db.ForeignKey("stations.id"), nullable=False)
    duration_minutes = db.Column(Integer, nullable=False)
    base_fare = db.Column(Float, nullable=False)
    is_active = db.Column(Boolean, default=True, nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

#relationships

    origin_station = relationship("transport_station", foreign_keys=[origin_station_id], back_populates="routes")
    schedules = relationship("transport_schedule", back_populates="route", cascade="all, delete-orphan", lazy="dynamic")


