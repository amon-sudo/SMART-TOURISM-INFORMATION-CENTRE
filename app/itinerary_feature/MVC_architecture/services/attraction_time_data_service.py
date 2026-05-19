"""
AttractionTimeDataService
Handles two data collection paths that feed avg_minutes:

  1. Operator input   — admin submits a form with their knowledge
  2. Analytics        — kiosk/app check-in/check-out events trigger an update

Both paths write to the attraction_time_data table.
The generator reads from this table via AttractionTimeData.best_for().
"""

from __future__ import annotations

from datetime import datetime

from app.extensions                 import db
from app.models.attraction_time_data import (
    AttractionTimeData, TimeDataSource,
)


class AttractionTimeDataService:

    # ── Operator input ─────────────────────────────────────────────────────────

    @staticmethod
    def submit_operator_input(
        attraction_id,
        avg_minutes: int,
        operator_notes: str | None = None,
        submitted_by=None,
    ) -> AttractionTimeData:
        """
        Called when an operator fills in the admin time-data form.
        Creates or updates the operator_input row for this attraction.

        Operator inputs start with confidence=0.8 — higher than AI estimates
        but lower than analytics with many samples.
        """
        if avg_minutes < 5 or avg_minutes > 1440:
            raise ValueError("avg_minutes must be between 5 and 1440 (24 hours)")

        row = AttractionTimeData.query.filter_by(
            attraction_id=attraction_id,
            source=TimeDataSource.OPERATOR_INPUT,
        ).first()

        if row:
            row.avg_minutes     = avg_minutes
            row.operator_notes  = operator_notes
            row.confidence      = 0.8
            row.updated_at      = datetime.utcnow()
        else:
            row = AttractionTimeData(
                attraction_id=attraction_id,
                source=TimeDataSource.OPERATOR_INPUT,
                avg_minutes=avg_minutes,
                confidence=0.8,
                sample_count=0,
                operator_notes=operator_notes,
            )
            db.session.add(row)

        db.session.commit()
        return row

    # ── Analytics ingestion ────────────────────────────────────────────────────

    @staticmethod
    def record_visit_duration(
        attraction_id,
        duration_minutes: int,
    ) -> AttractionTimeData:
        """
        Called by the analytics pipeline each time a visitor checks out
        of an attraction (derived from analytics_events check-in / check-out).

        Uses AttractionTimeData.upsert_analytics() which does a rolling
        average update and adjusts confidence automatically.

        Args:
            attraction_id   : UUID of the attraction
            duration_minutes: Actual visit duration derived from event timestamps
        """
        if duration_minutes < 1:
            # Ignore spurious sub-minute events (sensor glitches, accidental taps)
            return None

        # Cap at 8 hours to exclude overnight anomalies
        capped = min(duration_minutes, 480)

        return AttractionTimeData.upsert_analytics(attraction_id, capped)

    # ── Bulk analytics processing ──────────────────────────────────────────────

    @staticmethod
    def process_analytics_event_pair(
        attraction_id,
        checkin_at: datetime,
        checkout_at: datetime,
    ) -> AttractionTimeData | None:
        """
        Derive visit duration from a check-in / check-out event pair
        (typically sourced from the analytics_events table).

        Called by a background job or webhook after the checkout event fires.
        """
        if checkout_at <= checkin_at:
            return None

        delta_minutes = int((checkout_at - checkin_at).total_seconds() / 60)
        return AttractionTimeDataService.record_visit_duration(
            attraction_id, delta_minutes
        )

    # ── Read ───────────────────────────────────────────────────────────────────

    @staticmethod
    def get_all_for_attraction(attraction_id) -> list[AttractionTimeData]:
        """
        Return all time data rows for an attraction, ordered by confidence desc.
        Used in the admin panel to show all data sources side by side.
        """
        return (
            AttractionTimeData.query
            .filter_by(attraction_id=attraction_id)
            .order_by(AttractionTimeData.confidence.desc())
            .all()
        )

    @staticmethod
    def get_best_for_attraction(attraction_id) -> AttractionTimeData | None:
        """Proxy to the model class method for use in views."""
        return AttractionTimeData.best_for(attraction_id)


attraction_time_data_service = AttractionTimeDataService()
