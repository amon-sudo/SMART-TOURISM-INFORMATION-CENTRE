"""Aggregated module for the P4 endpoint backlog.

Exposes only the models at package import time. Blueprints are pulled from
``.routes`` lazily so that importing this package does not eagerly trigger
mapper configuration on downstream modules (e.g. feedback_media schemas).
Use ``from app.public_and_extras.routes import public_bp, extras_bp`` at
blueprint-registration time.
"""

from .models import (  # noqa: F401
    Favourite,
    Notification,
    AnalyticsEvent,
    UserActivity,
    DailyAnalyticsSnapshot,
)

__all__ = [
    "Favourite",
    "Notification",
    "AnalyticsEvent",
    "UserActivity",
    "DailyAnalyticsSnapshot",
]
