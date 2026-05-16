"""
AttractionTimeData model
Stores the average visit duration for an attraction, with source tracking,
confidence scoring, and sample counts so the generator always knows how
reliable a figure is before using it.

Sources (in priority order):
  1. operator_input  – filled in by the attraction operator via admin form
  2. analytics       – computed from kiosk check-in / check-out events
  3. ai_estimate     – estimated by Claude when no other data exists;
                       confidence starts low and gets replaced as real data arrives

One row per attraction per source. The generator picks the highest-confidence
row using AttractionTimeData.best_for(attraction_id).
"""

import enum
import uuid

from sqlalchemy import (
    Column, String, Integer, Float,
    DateTime, Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm                  import relationship

from app.extensions import db
from app.models.base import TimestampMixin, utcnow


class TimeDataSource(str, enum.Enum):
    OPERATOR_INPUT = "operator_input"
    ANALYTICS      = "analytics"
    AI_ESTIMATE    = "ai_estimate"


# Minimum confidence thresholds before a source is considered trustworthy
CONFIDENCE_THRESHOLDS = {
    TimeDataSource.OPERATOR_INPUT: 0.7,
    TimeDataSource.ANALYTICS:      0.5,
    TimeDataSource.AI_ESTIMATE:    0.0,   # always accepted as last resort
}

# Minimum analytics samples before analytics beats operator_input
MIN_ANALYTICS_SAMPLES = 10

# Category-level fallback defaults (minutes) used only inside the AI prompt
# to give Claude a sensible starting range if it has to estimate
CATEGORY_DEFAULTS = {
    "museum":          90,
    "heritage_site":   60,
    "national_park":  180,
    "wildlife":       240,
    "beach":          120,
    "cultural":        90,
    "restaurant":      60,
    "shopping":        90,
    "viewpoint":       30,
    "adventure":      180,
    "default":         90,
}


class AttractionTimeData(db.Model):
    __tablename__ = "attraction_time_data"

    __table_args__ = (
        UniqueConstraint(
            "attraction_id", "source",
            name="uq_attraction_time_data_attraction_source",
        ),
    )

    # ── Columns ──────────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    attraction_id = Column(
        UUID(as_uuid=True),
        db.ForeignKey("attractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Computed or reported average visit duration in minutes
    avg_minutes = Column(
        Integer,
        nullable=False,
        comment="Average visit duration in minutes",
    )

    source = Column(
        SAEnum(
            TimeDataSource,
            name="time_data_source_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )

    # 0.0 – 1.0. Rises as more real data arrives.
    # operator_input starts at 0.8, analytics at 0.4 rising with sample_count,
    # ai_estimate starts at 0.3.
    confidence = Column(
        Float,
        nullable=False,
        default=0.3,
        comment="Reliability score 0.0–1.0; higher = more trustworthy",
    )

    # Number of real visitor sessions that contributed to this average
    sample_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Analytics sample count; 0 for operator_input and ai_estimate",
    )

    # Free-text from the operator explaining their estimate
    operator_notes = Column(
        String(500),
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=utcnow, onupdate=utcnow)

    # ── Relationships ─────────────────────────────────────────────────────────
    attraction = relationship("Attraction", back_populates="time_data")

    # ── Class methods ─────────────────────────────────────────────────────────

    @classmethod
    def best_for(cls, attraction_id) -> "AttractionTimeData | None":
        """
        Return the most trustworthy time data row for an attraction.
        Priority: analytics (high samples) > operator_input > analytics (low) > ai_estimate.
        Returns None if no row exists at all.
        """
        rows = (
            cls.query
            .filter_by(attraction_id=attraction_id)
            .order_by(cls.confidence.desc(), cls.sample_count.desc())
            .all()
        )
        if not rows:
            return None

        # Prefer analytics if it has enough samples and high confidence
        analytics_row = next(
            (r for r in rows
             if r.source == TimeDataSource.ANALYTICS
             and r.sample_count >= MIN_ANALYTICS_SAMPLES),
            None,
        )
        if analytics_row:
            return analytics_row

        # Otherwise return highest-confidence row
        return rows[0]

    @classmethod
    def upsert_analytics(
        cls, attraction_id, new_duration_minutes: int
    ) -> "AttractionTimeData":
        """
        Called by the analytics pipeline after each visitor check-out.
        Incrementally recalculates the rolling average and updates confidence.
        """
        row = cls.query.filter_by(
            attraction_id=attraction_id,
            source=TimeDataSource.ANALYTICS,
        ).first()

        if row is None:
            row = cls(
                attraction_id=attraction_id,
                source=TimeDataSource.ANALYTICS,
                avg_minutes=new_duration_minutes,
                sample_count=1,
                confidence=0.2,
            )
            db.session.add(row)
        else:
            # Rolling average: new_avg = (old_avg * n + new_value) / (n + 1)
            n             = row.sample_count
            row.avg_minutes  = int((row.avg_minutes * n + new_duration_minutes) / (n + 1))
            row.sample_count = n + 1
            # Confidence rises with samples, capped at 0.95
            row.confidence   = min(0.2 + (row.sample_count / 100) * 0.75, 0.95)
            row.updated_at   = utcnow()

        db.session.commit()
        return row

    def __repr__(self) -> str:
        return (
            f"<AttractionTimeData attraction={self.attraction_id} "
            f"source={self.source} avg={self.avg_minutes}min "
            f"confidence={self.confidence:.2f}>"
        )
