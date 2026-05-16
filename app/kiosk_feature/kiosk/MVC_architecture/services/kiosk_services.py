"""
Kiosk Services
Three service classes covering every kiosk business operation:

  KioskService          — device registry, heartbeat, status management
  KioskSessionService   — session lifecycle, state updates, analytics logging
  KioskTransferService  — session-to-phone QR transfer (canonical implementation)
"""

from __future__ import annotations

import hashlib
import io
import os
import secrets
from datetime import datetime, timedelta

import qrcode
from nanoid import generate as nanoid_generate

from app.extensions import db
from app.models.kiosk import Kiosk, KioskStatus
from app.models.kiosk_session import KioskSession, KioskSessionStatus
from app.models.kiosk_session_transfer import (
    KioskSessionTransfer, TransferStatus, TRANSFER_TTL_MINUTES,
)
from app.models.kiosk_support_models import (
    KioskHealthLog, HealthEventType,
    KioskContentCache, ContentCacheStatus,
    KioskAnalyticsEvent,
)
from app.models.base import utcnow


# ─── KioskService ─────────────────────────────────────────────────────────────

class KioskService:
    """Device registry and health management."""

    # ── Registration & CRUD ──────────────────────────────────────────────────

    @staticmethod
    def register(
        name: str,
        location_type: str,
        address: str | None = None,
        business_profile_id=None,
        configuration: dict | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> Kiosk:
        """Register a new kiosk. Status starts as OFFLINE until first heartbeat."""
        from app.models.kiosk import KioskLocationType

        location = None
        if lat is not None and lng is not None:
            try:
                from geoalchemy2.elements import WKTElement
                location = WKTElement(f"POINT({lng} {lat})", srid=4326)
            except ImportError:
                location = f"{lat},{lng}"   # text fallback

        kiosk = Kiosk(
            name=name,
            location_type=KioskLocationType(location_type),
            address=address,
            business_profile_id=business_profile_id,
            configuration=configuration or {},
            location=location,
            status=KioskStatus.OFFLINE,
            installed_at=utcnow(),
        )
        db.session.add(kiosk)
        db.session.commit()
        return kiosk

    @staticmethod
    def list_kiosks(
        status: str | None = None,
        location_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ):
        """Paginated list of kiosks with optional filters."""
        query = Kiosk.query
        if status:
            query = query.filter_by(status=KioskStatus(status))
        if location_type:
            from app.models.kiosk import KioskLocationType
            query = query.filter_by(location_type=KioskLocationType(location_type))
        return query.order_by(Kiosk.name).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_or_404(kiosk_id) -> Kiosk:
        return Kiosk.query.get_or_404(kiosk_id, description="Kiosk not found")

    @staticmethod
    def update(kiosk_id, **kwargs) -> Kiosk:
        kiosk = KioskService.get_or_404(kiosk_id)
        allowed = {"name", "address", "location_type", "configuration", "status"}
        for key, val in kwargs.items():
            if key in allowed:
                setattr(kiosk, key, val)
        db.session.commit()
        return kiosk

    @staticmethod
    def decommission(kiosk_id) -> Kiosk:
        kiosk = KioskService.get_or_404(kiosk_id)
        return kiosk.decommission()

    # ── Heartbeat ────────────────────────────────────────────────────────────

    @staticmethod
    def record_heartbeat(kiosk_id, metrics: dict | None = None) -> Kiosk:
        """
        Called every 60 seconds by the kiosk agent.
        Updates last_heartbeat_at, sets status to ACTIVE if previously OFFLINE,
        and writes a KioskHealthLog row.
        """
        kiosk = KioskService.get_or_404(kiosk_id)

        previous_status = kiosk.status
        kiosk.record_heartbeat()   # updates last_heartbeat_at + status

        # Log the heartbeat event
        db.session.add(KioskHealthLog(
            kiosk_id=kiosk_id,
            event_type=HealthEventType.HEARTBEAT,
            metrics=metrics or {},
        ))

        # Log network recovery if kiosk was previously offline
        if previous_status == KioskStatus.OFFLINE:
            db.session.add(KioskHealthLog(
                kiosk_id=kiosk_id,
                event_type=HealthEventType.NETWORK_UP,
            ))

        db.session.commit()
        return kiosk

    @staticmethod
    def record_health_event(
        kiosk_id,
        event_type: str,
        metrics: dict | None = None,
        error_message: str | None = None,
    ) -> KioskHealthLog:
        """Log a non-heartbeat event (crash, startup, screen_on, etc.)."""
        log = KioskHealthLog(
            kiosk_id=kiosk_id,
            event_type=HealthEventType(event_type),
            metrics=metrics,
            error_message=error_message,
        )
        db.session.add(log)

        # Auto-set kiosk status on crash or shutdown
        if event_type == HealthEventType.CRASH.value:
            kiosk = KioskService.get_or_404(kiosk_id)
            kiosk.status = KioskStatus.OFFLINE

        db.session.commit()
        return log

    # ── Content cache sync ────────────────────────────────────────────────────

    @staticmethod
    def sync_content_cache(
        kiosk_id,
        content_type: str,
        payload: list,
    ) -> KioskContentCache:
        """
        Push a fresh content bundle to a kiosk's local cache.
        Called by the content sync job or triggered manually from admin.
        """
        version_hash = hashlib.md5(
            str(payload).encode(), usedforsecurity=False
        ).hexdigest()

        row = KioskContentCache.query.filter_by(
            kiosk_id=kiosk_id,
            content_type=content_type,
        ).first()

        if row:
            row.payload             = payload
            row.status              = ContentCacheStatus.CURRENT
            row.content_version     = version_hash
            row.last_synced_at      = utcnow()
            row.synced_record_count = len(payload)
        else:
            row = KioskContentCache(
                kiosk_id=kiosk_id,
                content_type=content_type,
                payload=payload,
                status=ContentCacheStatus.CURRENT,
                content_version=version_hash,
                last_synced_at=utcnow(),
                synced_record_count=len(payload),
            )
            db.session.add(row)

        db.session.commit()
        return row


# ─── KioskSessionService ──────────────────────────────────────────────────────

class KioskSessionService:
    """Session lifecycle management."""

    SESSION_TOKEN_BYTES = 32   # 256-bit session token

    @staticmethod
    def start_session(
        kiosk_id,
        ip_address: str | None = None,
        device_info: dict | None = None,
        user_id=None,
    ) -> KioskSession:
        """
        Start a new session. Called when the tourist first touches the screen.
        Generates a session_token for kiosk frontend API auth.
        """
        session_token = secrets.token_urlsafe(KioskSessionService.SESSION_TOKEN_BYTES)

        session = KioskSession(
            kiosk_id=kiosk_id,
            user_id=user_id,
            session_token=session_token,
            status=KioskSessionStatus.ACTIVE,
            ip_address=ip_address,
            device_info=device_info or {},
            state={"step": "home", "language": "en"},
        )
        db.session.add(session)
        db.session.commit()

        # Log session start analytics event
        KioskSessionService.log_event(
            session_id=session.id,
            kiosk_id=kiosk_id,
            event_type="session_started",
            screen="home",
        )

        return session

    @staticmethod
    def get_by_token(session_token: str) -> KioskSession | None:
        """Look up a session by its frontend token."""
        return KioskSession.query.filter_by(
            session_token=session_token,
            status=KioskSessionStatus.ACTIVE,
        ).first()

    @staticmethod
    def get_or_404(session_id) -> KioskSession:
        return KioskSession.query.get_or_404(session_id, description="Session not found")

    @staticmethod
    def update_state(session_id, patch: dict) -> KioskSession:
        """Merge a patch dict into the session's JSONB state."""
        session = KioskSessionService.get_or_404(session_id)
        return session.update_state(patch)

    @staticmethod
    def end_session(
        session_id,
        status: str = "completed",
    ) -> KioskSession:
        """End a session. Called on idle timeout, explicit exit, or transfer."""
        session = KioskSessionService.get_or_404(session_id)
        session.end(KioskSessionStatus(status))

        KioskSessionService.log_event(
            session_id=session_id,
            kiosk_id=session.kiosk_id,
            event_type="session_ended",
            metadata={"status": status, "duration_seconds": session.duration_seconds},
        )
        return session

    @staticmethod
    def log_event(
        session_id,
        kiosk_id,
        event_type: str,
        screen: str | None = None,
        metadata: dict | None = None,
    ) -> KioskAnalyticsEvent:
        """Write one analytics event row. Call this on every meaningful tourist action."""
        event = KioskAnalyticsEvent(
            session_id=session_id,
            kiosk_id=kiosk_id,
            event_type=event_type,
            screen=screen,
            metadata=metadata or {},
        )
        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def get_session_analytics(kiosk_id, from_date=None, to_date=None) -> dict:
        """
        Aggregate analytics for the admin dashboard.
        Returns counts by event_type and popular screens.
        """
        from sqlalchemy import func

        query = (
            db.session.query(
                KioskAnalyticsEvent.event_type,
                func.count(KioskAnalyticsEvent.id).label("count"),
            )
            .filter_by(kiosk_id=kiosk_id)
        )
        if from_date:
            query = query.filter(KioskAnalyticsEvent.occurred_at >= from_date)
        if to_date:
            query = query.filter(KioskAnalyticsEvent.occurred_at <= to_date)

        results = query.group_by(KioskAnalyticsEvent.event_type).all()
        return {row.event_type: row.count for row in results}


# ─── KioskTransferService ─────────────────────────────────────────────────────

class KioskTransferService:
    """
    Kiosk-to-phone session transfer.
    Uses KioskSessionTransfer (canonical) instead of HandoffToken.
    """

    TOKEN_LENGTH = 32

    @staticmethod
    def create_transfer(kiosk_session_id) -> KioskSessionTransfer:
        """
        Generate a one-time QR for session transfer.
        Revokes any existing pending transfers for this session first.
        """
        # Load session to snapshot its current state
        session = KioskSession.query.get_or_404(
            kiosk_session_id, description="Session not found"
        )

        # Revoke existing pending transfers
        KioskSessionTransfer.revoke_pending_for_session(kiosk_session_id)

        # Generate token + URL
        token       = nanoid_generate(size=KioskTransferService.TOKEN_LENGTH)
        base_url    = os.getenv("APP_BASE_URL", "http://localhost:5000")
        transfer_url = f"{base_url}/api/sessions/transfer/{token}"

        # Render QR image
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(transfer_url)
        qr.make(fit=True)
        img    = qr.make_image(fill_color="#003366", back_color="#FFFFFF")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        from app.services.storage import StorageService
        qr_image_path = StorageService.upload(
            buffer=buffer,
            filename=f"transfers/{kiosk_session_id}/{token}.png",
            mime_type="image/png",
        )

        # Persist
        transfer = KioskSessionTransfer(
            kiosk_session_id=kiosk_session_id,
            user_id=session.user_id,
            token=token,
            session_snapshot=session.state or {},
            transfer_url=transfer_url,
            qr_image_path=qr_image_path,
            status=TransferStatus.PENDING,
            expires_at=utcnow() + timedelta(minutes=TRANSFER_TTL_MINUTES),
        )
        db.session.add(transfer)
        db.session.commit()

        # Log analytics event
        KioskSessionService.log_event(
            session_id=kiosk_session_id,
            kiosk_id=session.kiosk_id,
            event_type="transfer_qr_generated",
            screen=session.state.get("step") if session.state else None,
        )

        return transfer

    @staticmethod
    def redeem_transfer(token: str, mobile_ip: str | None = None) -> dict:
        """
        Called when the phone scans the QR.
        Burns the token, issues a 15-minute mobile JWT, returns session state.
        """
        from flask_jwt_extended import create_access_token

        transfer = KioskSessionTransfer.query.filter_by(token=token).first()
        if not transfer:
            raise ValueError("Transfer QR not found. It may have expired.")

        transfer.redeem(mobile_ip=mobile_ip)

        # Mark the kiosk session as transferred
        session = KioskSession.query.get(transfer.kiosk_session_id)
        if session:
            session.end(KioskSessionStatus.TRANSFERRED)
            KioskSessionService.log_event(
                session_id=transfer.kiosk_session_id,
                kiosk_id=session.kiosk_id,
                event_type="session_transferred",
                metadata={"mobile_ip": mobile_ip},
            )

        # Issue mobile JWT — no username/password needed
        mobile_jwt = create_access_token(
            identity=str(transfer.kiosk_session_id),
            expires_delta=timedelta(minutes=15),
            additional_claims={
                "type":             "session_transfer",
                "kiosk_session_id": str(transfer.kiosk_session_id),
                "transfer_id":      str(transfer.id),
            },
        )

        base_url = os.getenv("APP_BASE_URL", "http://localhost:5000")
        return {
            "mobile_jwt":       mobile_jwt,
            "jwt_expires_in":   900,
            "kiosk_session_id": str(transfer.kiosk_session_id),
            "session_state":    transfer.session_snapshot,
            "resume_url":       f"tourism-app://resume?session={transfer.kiosk_session_id}",
            "web_resume_url":   f"{base_url}/mobile/resume/{transfer.kiosk_session_id}",
        }

    @staticmethod
    def get_transfer_status(kiosk_session_id) -> dict:
        """Kiosk polls this to know when the phone has scanned."""
        latest = (
            KioskSessionTransfer.query
            .filter_by(kiosk_session_id=kiosk_session_id)
            .order_by(KioskSessionTransfer.created_at.desc())
            .first()
        )
        if not latest:
            return {"transferred": False, "status": "none", "used_at": None}

        if latest.status == TransferStatus.PENDING and latest.is_expired:
            latest.status = TransferStatus.EXPIRED
            db.session.commit()

        return {
            "transferred": latest.status == TransferStatus.REDEEMED,
            "status":      latest.status.value,
            "used_at":     latest.used_at.isoformat() if latest.used_at else None,
        }


# Module-level singletons
kiosk_service    = KioskService()
session_service  = KioskSessionService()
transfer_service = KioskTransferService()
