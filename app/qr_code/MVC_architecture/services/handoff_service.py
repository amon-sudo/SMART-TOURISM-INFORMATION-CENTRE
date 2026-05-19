"""
HandoffService
Manages kiosk-to-phone session transfer via one-time QR codes.

Three public methods:

  create_handoff(kiosk_session_id, session_state)
      Called by the kiosk when the tourist taps "Continue on phone".
      Saves session state, generates a burn-once QR, returns the token.

  redeem_handoff(token, mobile_ip)
      Called when the phone scans the QR (GET /api/handoff/<token>).
      Validates, burns the token, issues a mobile JWT, returns session state.

  get_handoff_status(kiosk_session_id)
      Called by the kiosk polling to know if the phone has scanned yet.
      Returns { transferred: bool, used_at: datetime | None }

Dependencies (already in requirements.txt):
    qrcode[pil]   – QR image rendering
    nanoid        – short token generation
    flask-jwt-extended – mobile JWT issuance
"""

from __future__ import annotations

import io
import os
from datetime import datetime, timedelta, timezone

import qrcode
from nanoid                import generate as nanoid_generate
from flask_jwt_extended    import create_access_token

from app.extensions import db
from app.kiosk_feature.kiosk.MVC_architecture.models.kiosk_session_transfer import (
    KioskSessionTransfer,
    TransferStatus,
    TRANSFER_TTL_MINUTES,
)

TOKEN_LENGTH        = 32    # longer than QR tokens — single-use so harder to guess
MOBILE_JWT_MINUTES  = 15    # phone JWT expires in 15 minutes


class HandoffService:

    @staticmethod
    def _store_qr_image(buffer: io.BytesIO, kiosk_session_id, token: str) -> str:
        """Persist QR PNG to local storage and return a relative URL path."""
        base_dir = "/tmp/tourism_qr_codes"
        rel_path = f"handoff/{kiosk_session_id}/{token}.png"
        full_path = os.path.join(base_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(buffer.getvalue())
        return f"/{rel_path}"

    # ── Create ────────────────────────────────────────────────────────────────

    @staticmethod
    def create_handoff(
        kiosk_session_id,
        session_state: dict,
    ) -> KioskSessionTransfer:
        """
        Generate a one-time handoff token + QR image for a kiosk session.

        Steps:
          1. Revoke any existing pending tokens for this session
             (tourist tapped "Resend" — old QR is dead)
          2. Generate a short random token
          3. Build the handoff URL
          4. Render a QR image and store it
                    5. Persist the kiosk_session_transfers row
          6. Return the token (controller serialises it for the kiosk screen)

        Args:
            kiosk_session_id : UUID of the active kiosk_sessions row
            session_state    : Full dict of the current kiosk UI state
                               (step, destination, interests, itinerary_draft, etc.)

        Returns:
            KioskSessionTransfer instance (uses transfer_url and qr_image_path)
        """
        kiosk_session_id = str(kiosk_session_id)

        # Step 1: invalidate any live pending tokens for this session
        KioskSessionTransfer.revoke_pending_for_session(kiosk_session_id)

        # Step 2: generate token
        token = nanoid_generate(size=TOKEN_LENGTH)

        # Step 3: build URL
        base_url    = os.getenv("APP_BASE_URL", "http://localhost:5000")
        handoff_url = f"{base_url}/api/v1/handoff/{token}"

        # Step 4: render QR image
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(handoff_url)
        qr.make(fit=True)
        img    = qr.make_image(fill_color="#003366", back_color="#FFFFFF")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qr_image_path = HandoffService._store_qr_image(buffer, kiosk_session_id, token)

        # Step 5: persist
        from app.qr_code.MVC_architecture.models.base import utcnow
        handoff = KioskSessionTransfer(
            kiosk_session_id=kiosk_session_id,
            token=token,
            user_id=None,
            session_snapshot=session_state,
            qr_image_path=qr_image_path,
            transfer_url=handoff_url,
            status=TransferStatus.PENDING,
            expires_at=utcnow() + timedelta(minutes=TRANSFER_TTL_MINUTES),
        )
        db.session.add(handoff)
        db.session.commit()

        return handoff

    # ── Redeem ────────────────────────────────────────────────────────────────

    @staticmethod
    def redeem_handoff(
        token: str,
        mobile_ip: str | None = None,
    ) -> dict:
        """
        Called when the phone hits GET /api/handoff/<token>.

        Steps:
          1. Look up the token
          2. Call token.redeem() — raises ValueError for invalid/expired/used
          3. Issue a short-lived mobile JWT (15 min)
             JWT additional claims carry kiosk_session_id so the mobile app
             can fetch state and resume the session
          4. Return everything the mobile app needs to reconstruct the session

        Args:
            token     : The raw token string from the URL
            mobile_ip : Request remote IP for audit logging

        Returns:
            {
              "mobile_jwt":        "<jwt>",
              "jwt_expires_in":    900,          # seconds
              "kiosk_session_id":  "<uuid>",
              "session_state":     { ... },      # full kiosk state
              "resume_url":        "tourism-app://resume?session=<uuid>"
            }

        Raises:
            ValueError : token invalid, already used, or expired
        """
        handoff = KioskSessionTransfer.query.filter_by(token=token).first()

        if handoff is None:
            raise ValueError("Handoff QR not found. It may have expired or never existed.")

        # Burns the token (raises ValueError for bad states)
        handoff.redeem(mobile_ip=mobile_ip)

        # Issue mobile JWT — identity = kiosk_session_id (no user account needed)
        mobile_jwt = create_access_token(
            identity=str(handoff.kiosk_session_id),
            expires_delta=timedelta(minutes=MOBILE_JWT_MINUTES),
            additional_claims={
                "type":             "handoff",
                "kiosk_session_id": str(handoff.kiosk_session_id),
                "handoff_id":       str(handoff.id),
            },
        )

        base_url   = os.getenv("APP_BASE_URL", "http://localhost:5000")
        resume_url = f"tourism-app://resume?session={handoff.kiosk_session_id}"

        return {
            "mobile_jwt":       mobile_jwt,
            "jwt_expires_in":   MOBILE_JWT_MINUTES * 60,
            "kiosk_session_id": str(handoff.kiosk_session_id),
            "session_state":    handoff.session_snapshot,
            "resume_url":       resume_url,
            # Fallback web URL if the mobile app is not installed
            "web_resume_url":   f"{base_url}/mobile/resume/{handoff.kiosk_session_id}",
        }

    # ── Status polling ────────────────────────────────────────────────────────

    @staticmethod
    def get_handoff_status(kiosk_session_id) -> dict:
        """
        Called by the kiosk polling GET /api/sessions/<id>/handoff-status.
        The kiosk shows a spinner until transferred=True, then displays:
        "Session sent to your phone ✓"

        Returns:
            {
              "transferred": bool,
              "used_at":     "2024-06-01T09:15:30Z" | None,
              "status":      "pending" | "redeemed" | "expired" | "revoked"
            }
        """
        kiosk_session_id = str(kiosk_session_id)

        # Get the most recent handoff token for this session
        latest = (
            KioskSessionTransfer.query
            .filter_by(kiosk_session_id=kiosk_session_id)
            .order_by(KioskSessionTransfer.created_at.desc())
            .first()
        )

        if latest is None:
            return {
                "transferred": False,
                "used_at":     None,
                "status":      "none",
            }

        # Auto-expire stale pending tokens on status check
        if latest.status == TransferStatus.PENDING and latest.is_expired:
            latest.status = TransferStatus.EXPIRED
            db.session.commit()

        return {
            "transferred": latest.status == TransferStatus.REDEEMED,
            "used_at":     latest.used_at.isoformat() if latest.used_at else None,
            "status":      latest.status.value,
        }

    # ── Data URL helper (kiosk inline display) ────────────────────────────────

    @staticmethod
    def to_data_url(handoff_url: str) -> str:
        """
        Generate a base64 PNG data URL for embedding directly in the kiosk HTML.
        Used when the kiosk renders the QR inline without a storage round-trip.
        """
        import base64
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(handoff_url)
        qr.make(fit=True)
        img    = qr.make_image(fill_color="#003366", back_color="#FFFFFF")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64    = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"


# Module-level singleton
handoff_service = HandoffService()
