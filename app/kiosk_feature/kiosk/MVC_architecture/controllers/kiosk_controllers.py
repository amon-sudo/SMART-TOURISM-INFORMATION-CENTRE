"""
Kiosk Controllers
Three controllers, each with a single responsibility:

  KioskController         — device registry CRUD + heartbeat + admin ops
  KioskSessionController  — session lifecycle + state updates + analytics
  KioskTransferController — session-to-phone QR transfer
"""

from __future__ import annotations

from flask              import request, redirect
from flask_jwt_extended import get_jwt_identity, get_jwt

from app.services.kiosk_services import kiosk_service, session_service, transfer_service
from app.validators.kiosk_schemas import (
    KioskCreateSchema, KioskUpdateSchema, KioskListQuerySchema,
    HeartbeatSchema, HealthEventSchema, ContentSyncSchema,
    SessionStartSchema, SessionStateUpdateSchema,
    SessionAnalyticsQuerySchema,
)
from app.utils.api_response import success, created, bad_request
from app.utils.pagination   import paginate_query


# ── Schema instances ──────────────────────────────────────────────────────────
_kiosk_create   = KioskCreateSchema()
_kiosk_update   = KioskUpdateSchema()
_kiosk_list_q   = KioskListQuerySchema()
_heartbeat      = HeartbeatSchema()
_health_event   = HealthEventSchema()
_content_sync   = ContentSyncSchema()
_session_start  = SessionStartSchema()
_state_update   = SessionStateUpdateSchema()
_analytics_q    = SessionAnalyticsQuerySchema()


# ═══════════════════════════════════════════════════════════════════════════════
#  KIOSK CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

def register_kiosk():
    """
    POST /api/admin/kiosks
    Register a new physical kiosk device.
    """
    data  = _kiosk_create.load(request.get_json(force=True) or {})
    kiosk = kiosk_service.register(**data)
    return created(_serialise_kiosk(kiosk))


def list_kiosks():
    """GET /api/admin/kiosks  — paginated list with filters."""
    args   = _kiosk_list_q.load(request.args)
    result = kiosk_service.list_kiosks(
        status=args.get("status"),
        location_type=args.get("location_type"),
        page=args["page"],
        per_page=args["per_page"],
    )
    return success({
        "data":        [_serialise_kiosk(k) for k in result.items],
        "total":       result.total,
        "page":        result.page,
        "per_page":    result.per_page,
        "total_pages": result.pages,
    })


def show_kiosk(kiosk_id: str):
    """GET /api/admin/kiosks/<kiosk_id>"""
    kiosk = kiosk_service.get_or_404(kiosk_id)
    return success(_serialise_kiosk(kiosk))


def update_kiosk(kiosk_id: str):
    """PATCH /api/admin/kiosks/<kiosk_id>"""
    data  = _kiosk_update.load(request.get_json(force=True) or {})
    kiosk = kiosk_service.update(kiosk_id, **data)
    return success(_serialise_kiosk(kiosk))


def decommission_kiosk(kiosk_id: str):
    """POST /api/admin/kiosks/<kiosk_id>/decommission"""
    kiosk = kiosk_service.decommission(kiosk_id)
    return success({"message": f"Kiosk {kiosk.name} decommissioned", "status": kiosk.status.value})


def receive_heartbeat(kiosk_id: str):
    """
    POST /api/kiosks/<kiosk_id>/heartbeat
    Called every 60 seconds by the kiosk agent.
    Body: { metrics: { cpu_percent, ram_percent, disk_percent, ... } }
    """
    data  = _heartbeat.load(request.get_json(force=True) or {})
    kiosk = kiosk_service.record_heartbeat(kiosk_id, metrics=data.get("metrics"))
    return success({
        "status":            kiosk.status.value,
        "last_heartbeat_at": kiosk.last_heartbeat_at.isoformat(),
        "is_online":         kiosk.is_online,
    })


def receive_health_event(kiosk_id: str):
    """
    POST /api/kiosks/<kiosk_id>/health-events
    Body: { event_type, metrics?, error_message? }
    """
    data = _health_event.load(request.get_json(force=True) or {})
    log  = kiosk_service.record_health_event(kiosk_id, **data)
    return created({
        "id":         str(log.id),
        "event_type": log.event_type.value,
        "recorded_at": log.recorded_at.isoformat(),
    })


def sync_content(kiosk_id: str):
    """
    POST /api/admin/kiosks/<kiosk_id>/content-sync
    Push a fresh content bundle to the kiosk's offline cache.
    Body: { content_type, payload: [...] }
    """
    data  = _content_sync.load(request.get_json(force=True) or {})
    cache = kiosk_service.sync_content_cache(kiosk_id, **data)
    return success({
        "content_type":       cache.content_type,
        "status":             cache.status.value,
        "synced_record_count": cache.synced_record_count,
        "last_synced_at":     cache.last_synced_at.isoformat(),
    })


def get_offline_content(kiosk_id: str, content_type: str):
    """
    GET /api/kiosks/<kiosk_id>/content/<content_type>
    Kiosk fetches its local cache bundle for offline serving.
    """
    from app.models.kiosk_support_models import KioskContentCache
    cache = KioskContentCache.query.filter_by(
        kiosk_id=kiosk_id,
        content_type=content_type,
    ).first()
    if not cache:
        return bad_request(f"No content cache found for type: {content_type}")
    return success({
        "content_type": cache.content_type,
        "payload":      cache.payload,
        "status":       cache.status.value,
        "last_synced_at": cache.last_synced_at.isoformat() if cache.last_synced_at else None,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

def start_session(kiosk_id: str):
    """
    POST /api/kiosks/<kiosk_id>/sessions
    Called when a tourist first touches the kiosk screen.
    Body: { device_info?, user_id? }
    Returns session_token for use in subsequent kiosk API calls.
    """
    data    = _session_start.load(request.get_json(force=True) or {})
    session = session_service.start_session(
        kiosk_id=kiosk_id,
        ip_address=request.remote_addr,
        device_info=data.get("device_info"),
        user_id=data.get("user_id"),
    )
    return created({
        "session_id":    str(session.id),
        "session_token": session.session_token,
        "started_at":    session.started_at.isoformat(),
        "status":        session.status.value,
        "state":         session.state,
    })


def update_session_state(session_id: str):
    """
    PATCH /api/sessions/<session_id>/state
    Kiosk frontend calls this on every screen transition.
    Body: { step, language, destination, interests, ... }
    """
    data    = _state_update.load(request.get_json(force=True) or {})
    session = session_service.update_state(session_id, data["state_patch"])
    return success({"state": session.state})


def end_session(session_id: str):
    """
    POST /api/sessions/<session_id>/end
    Body: { status: "completed" | "expired" | "transferred" }
    """
    data    = request.get_json(force=True) or {}
    status  = data.get("status", "completed")
    session = session_service.end_session(session_id, status=status)
    return success({
        "session_id":       str(session.id),
        "status":           session.status.value,
        "duration_seconds": session.duration_seconds,
    })


def log_analytics_event(session_id: str):
    """
    POST /api/sessions/<session_id>/events
    Body: { event_type, screen?, metadata? }
    High-frequency endpoint — called on every tourist interaction.
    """
    data  = request.get_json(force=True) or {}
    event_type = data.get("event_type")
    if not event_type:
        return bad_request("event_type is required")

    session = session_service.get_or_404(session_id)
    event   = session_service.log_event(
        session_id=session_id,
        kiosk_id=session.kiosk_id,
        event_type=event_type,
        screen=data.get("screen"),
        metadata=data.get("metadata"),
    )
    return created({"id": str(event.id), "event_type": event.event_type})


def get_analytics(kiosk_id: str):
    """
    GET /api/admin/kiosks/<kiosk_id>/analytics
    Admin: aggregated event counts for the dashboard.
    Query params: from_date, to_date
    """
    args   = _analytics_q.load(request.args)
    result = session_service.get_session_analytics(
        kiosk_id=kiosk_id,
        from_date=args.get("from_date"),
        to_date=args.get("to_date"),
    )
    return success({"kiosk_id": str(kiosk_id), "events": result})


# ═══════════════════════════════════════════════════════════════════════════════
#  TRANSFER CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

def create_transfer(session_id: str):
    """
    POST /api/sessions/<session_id>/transfer
    Tourist taps "Continue on phone". Kiosk calls this.
    Returns QR data URL to display on screen + expires_in countdown.
    """
    try:
        transfer = transfer_service.create_transfer(session_id)
    except Exception as e:
        return bad_request(str(e))

    # Inline data URL so kiosk can render without a storage round-trip
    from app.services.kiosk_services import KioskTransferService
    import qrcode, io, base64
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(transfer.transfer_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#003366", back_color="#FFFFFF")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    return created({
        "transfer_id":   str(transfer.id),
        "transfer_url":  transfer.transfer_url,
        "qr_data_url":   data_url,
        "expires_in":    300,
        "status":        transfer.status.value,
    })


def redeem_transfer(token: str):
    """
    GET /api/sessions/transfer/<token>
    Phone scans the QR. No auth required — token is the credential.
    Burns the token and issues a 15-minute mobile JWT.
    """
    mobile_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    try:
        result = transfer_service.redeem_transfer(token, mobile_ip=mobile_ip)
    except ValueError as e:
        accept = request.headers.get("Accept", "")
        if "text/html" in accept:
            base_url = os.getenv("APP_BASE_URL", "http://localhost:5000")
            return redirect(f"{base_url}/transfer-error?reason={e}", 302)
        return bad_request(str(e))

    # Phone browser → redirect to deep-link
    accept = request.headers.get("Accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return redirect(result["resume_url"], 302)

    return success(result)


def get_transfer_status(session_id: str):
    """
    GET /api/sessions/<session_id>/transfer-status
    Kiosk polls every 2 seconds to know when the phone has scanned.
    """
    status = transfer_service.get_transfer_status(session_id)
    return success(status)


# ── Serialiser ────────────────────────────────────────────────────────────────
def _serialise_kiosk(kiosk) -> dict:
    return {
        "id":                   str(kiosk.id),
        "name":                 kiosk.name,
        "address":              kiosk.address,
        "location_type":        kiosk.location_type.value,
        "status":               kiosk.status.value,
        "is_online":            kiosk.is_online,
        "last_heartbeat_at":    kiosk.last_heartbeat_at.isoformat() if kiosk.last_heartbeat_at else None,
        "installed_at":         kiosk.installed_at.isoformat() if kiosk.installed_at else None,
        "decommissioned_at":    kiosk.decommissioned_at.isoformat() if kiosk.decommissioned_at else None,
        "configuration":        kiosk.configuration,
        "business_profile_id":  str(kiosk.business_profile_id) if kiosk.business_profile_id else None,
        "created_at":           kiosk.created_at.isoformat(),
    }


import os
