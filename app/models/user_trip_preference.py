import uuid

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class UserTripPreference(BaseModel):
    __tablename__ = "user_trip_preferences"

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    trip_duration = Column(Integer, nullable=False, default=1)
    budget_level = Column(String(20), nullable=False, default="medium")
    interests = Column(String(500), nullable=True)
    pace = Column(String(20), nullable=False, default="moderate")
