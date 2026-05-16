"""
ItineraryDayAttraction model
Bridge between itinerary_days and attractions.
Each row represents one attraction visit within a day, with:
  - Scheduled start time
  - Expected duration (from AttractionTimeData, copied at generation time)
  - Visit order within the day
  - AI-generated per-attraction narrative note

This table is what allows the kiosk and mobile app to display:
  "Day 1 — 9:00am  Karen Blixen Museum (90 min)
            11:00am Giraffe Centre (60 min)
            1:00pm  Carnivore Restaurant (90 min)"
"""

import uuid
from sqlalchemy import Column, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm                  import relationship

from app.extensions import db


class ItineraryDayAttraction(db.Model):
    __tablename__ = "itinerary_day_attractions"

    # ── Columns ──────────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    itinerary_day_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("itinerary_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attraction_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("attractions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # 1-based position within the day's schedule
    visit_order = Column(
        Integer,
        nullable=False,
        comment="Visit order within the day (1 = first stop)",
    )

    # Scheduled arrival time e.g. 09:00:00
    start_time = Column(
        Time,
        nullable=False,
        comment="Planned arrival time at this attraction",
    )

    # Duration snapshot from AttractionTimeData at generation time.
    # Stored here so the plan stays consistent even if AttractionTimeData
    # is later updated.
    duration_minutes = Column(
        Integer,
        nullable=False,
        comment="Expected visit duration in minutes (snapshot from AttractionTimeData)",
    )

    # AI-generated per-stop narrative, e.g.:
    # "Start your morning at the Karen Blixen Museum, where you can explore
    #  colonial history and the life of the famous Danish author."
    narrative_note = Column(
        Text,
        nullable=True,
        comment="AI-generated per-attraction narrative for the tourist",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    attraction = relationship(
        "Attraction",
        lazy="joined",   # always load with parent — needed for display
    )

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def end_time(self):
        """Computed end time = start_time + duration_minutes."""
        from datetime import datetime, timedelta
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt   = start_dt + timedelta(minutes=self.duration_minutes)
        return end_dt.time()

    def to_dict(self) -> dict:
        return {
            "id":               str(self.id),
            "attraction_id":    str(self.attraction_id),
            "attraction_name":  self.attraction.name if self.attraction else None,
            "visit_order":      self.visit_order,
            "start_time":       self.start_time.strftime("%H:%M") if self.start_time else None,
            "end_time":         self.end_time.strftime("%H:%M"),
            "duration_minutes": self.duration_minutes,
            "narrative_note":   self.narrative_note,
        }

    def __repr__(self) -> str:
        return (
            f"<ItineraryDayAttraction day={self.itinerary_day_id} "
            f"order={self.visit_order} attraction={self.attraction_id}>"
        )
