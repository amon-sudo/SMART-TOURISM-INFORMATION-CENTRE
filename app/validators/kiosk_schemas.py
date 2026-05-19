"""Re-export of kiosk marshmallow schemas at their legacy import path."""

from app.kiosk_feature.kiosk.validators.kiosk_schemas import (  # noqa: F401
    KioskCreateSchema,
    KioskUpdateSchema,
    KioskListQuerySchema,
    MetricsSchema,
    HeartbeatSchema,
    HealthEventSchema,
    ContentSyncSchema,
    SessionStartSchema,
    SessionStateUpdateSchema,
    SessionAnalyticsQuerySchema,
    MaintenanceLogSchema,
)
