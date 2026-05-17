"""Re-export of Kiosk model at its legacy import path."""

from app.kiosk_feature.kiosk.MVC_architecture.models.kiosk import (  # noqa: F401
    Kiosk,
    KioskStatus,
    KioskLocationType,
    HEARTBEAT_TIMEOUT_MINUTES,
)
