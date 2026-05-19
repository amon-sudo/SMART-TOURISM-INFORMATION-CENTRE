"""Re-export of KioskSessionTransfer model at its legacy import path."""

from app.kiosk_feature.kiosk.MVC_architecture.models.kiosk_session_transfer import (  # noqa: F401
    KioskSessionTransfer,
    TransferStatus,
    TRANSFER_TTL_MINUTES,
)
