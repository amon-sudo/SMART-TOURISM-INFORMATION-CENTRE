"""Re-export of kiosk support models at their legacy import path."""

from app.kiosk_feature.kiosk.MVC_architecture.models.kiosk_support_models import (  # noqa: F401
    HealthEventType,
    KioskHealthLog,
    MaintenanceType,
    KioskMaintenanceLog,
    ContentCacheStatus,
    KioskContentCache,
    KioskAnalyticsEvent,
)
