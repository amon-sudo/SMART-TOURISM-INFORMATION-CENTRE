"""Re-export of kiosk service singletons at their legacy import path."""

from app.kiosk_feature.kiosk.MVC_architecture.services.kiosk_services import (  # noqa: F401
    KioskService,
    KioskSessionService,
    KioskTransferService,
    kiosk_service,
    session_service,
    transfer_service,
)
