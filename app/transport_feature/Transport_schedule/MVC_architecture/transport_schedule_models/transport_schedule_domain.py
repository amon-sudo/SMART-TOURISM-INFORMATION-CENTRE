import uuid
from datetime import datetime
from app.extensions import db
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Uuid
from sqlalchemy.orm import relationship

class transport_schedule(db.Model):
    __tablename__ = "transport_schedules"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numeric_id = db.Column(Integer, unique=True, nullable=False, index=True)
    transport_route_id = db.Column(Uuid(as_uuid=True), ForeignKey("transport_routes.id"), nullable=False)
    departure_time = db.Column(DateTime, nullable=False)
    arrival_time = db.Column(DateTime, nullable=False)
    available_seats = db.Column(Integer, nullable=False)
    price = db.Column(Float, nullable=False)
    is_active = db.Column(Boolean, default=True, nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


#relationships

    route = relationship("TransportRoute", back_populates="schedules")
