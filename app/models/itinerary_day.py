import uuid

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.extensions import db
from app.models.base import BaseModel


class ItineraryDay(BaseModel):
    __tablename__ = "itinerary_days"

    itinerary_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("itineraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    day_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    narrative = Column(Text, nullable=True)

    itinerary = relationship("Itinerary")
    day_attractions = relationship(
        "ItineraryDayAttraction",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ItineraryDayAttraction.visit_order",
    )
