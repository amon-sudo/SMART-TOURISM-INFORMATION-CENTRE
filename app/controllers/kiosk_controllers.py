"""Re-export of the kiosk controllers at their legacy import path."""

from app.kiosk_feature.kiosk.MVC_architecture.controllers.kiosk_controllers import (  # noqa: F401
    # Kiosk device
    register_kiosk,
    list_kiosks,
    show_kiosk,
    update_kiosk,
    decommission_kiosk,
    receive_heartbeat,
    receive_health_event,
    sync_content,
    get_offline_content,
    get_analytics,
    # Session
    start_session,
    update_session_state,
    end_session,
    log_analytics_event,
    # Transfer
    create_transfer,
    redeem_transfer,
    get_transfer_status,
)
