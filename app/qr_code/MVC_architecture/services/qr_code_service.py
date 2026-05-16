"""
QrCodeService
Business logic for generating, refreshing, and resolving QR codes.

Dependencies (add to requirements.txt):
    qrcode[pil]>=7.4
    nanoid>=2.0
    Pillow>=10.0
"""

from __future__ import annotations

import io
import os
from datetime import datetime

import qrcode
from qrcode.image.pil     import PilImage
from nanoid                import generate as nanoid_generate

from app.extensions                              import db
from app.qr_code.MVC_architecture.models.qr_code import QrCode, QrCodeStatus, QrTargetType

TOKEN_LENGTH = 24  # characters in the short URL token


class LocalStorageService:
    """Simple local file storage for QR images."""
    
    BASE_DIR = "/tmp/tourism_qr_codes"
    
    @staticmethod
    def upload(buffer, filename: str, mime_type: str = None) -> str:
        """
        Save a buffer to local filesystem.
        Returns the relative path for database storage.
        """
        # Create directory structure if needed
        full_path = os.path.join(LocalStorageService.BASE_DIR, filename)
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)
        
        # Write file
        with open(full_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        # Return relative path for database
        return f"/{filename}"


# Alias for convenience
StorageService = LocalStorageService


class QrCodeService:
    """
    Centralised QR code management.
    All QR code creation and revocation MUST go through this service
    to keep token uniqueness, storage, and referential integrity consistent.
    """

    # ── Generation ────────────────────────────────────────────────────────────

    @staticmethod
    def generate_or_refresh(
        target_type: str,
        target_id,
        created_by=None,
        force_new: bool = False,
        expires_at: datetime | None = None,
    ) -> QrCode:
        """
        Return an active QR code for (target_type, target_id).
        If one already exists and force_new is False, return it directly.
        If force_new is True, revoke the existing code and issue a fresh one.

        Args:
            target_type : 'itinerary' | 'booking' | 'kiosk_session'
            target_id   : UUID of the owning entity
            created_by  : UUID of the requesting user (None = system)
            force_new   : Always create a fresh QR record
            expires_at  : Optional expiry; None = never expires

        Returns:
            QrCode instance
        """
        target_type_enum = QrTargetType(target_type)

        # ── Dedup: reuse existing active code unless force_new ────────────────
        if not force_new:
            existing = (
                QrCode.query
                .filter_by(
                    target_type=target_type_enum,
                    target_id=target_id,
                    status=QrCodeStatus.ACTIVE,
                )
                .order_by(QrCode.created_at.desc())
                .first()
            )
            if existing:
                return existing

        # Revoke existing active codes for this entity before issuing new one
        (
            QrCode.query
            .filter_by(
                target_type=target_type_enum,
                target_id=target_id,
                status=QrCodeStatus.ACTIVE,
            )
            .update({"status": QrCodeStatus.REVOKED}, synchronize_session=False)
        )

        # ── Generate token + URL ──────────────────────────────────────────────
        token = nanoid_generate(size=TOKEN_LENGTH)
        base_url = os.getenv("APP_BASE_URL", "http://localhost:5000")
        url = f"{base_url}/api/public/qr/{token}/scan"

        # ── Render QR image ───────────────────────────────────────────────────
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Kenya tourism brand colours: dark navy / white
        img: PilImage = qr.make_image(
            fill_color="#003366",
            back_color="#FFFFFF",
        )
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # ── Persist image ─────────────────────────────────────────────────────
        image_path = StorageService.upload(
            buffer=buffer,
            filename=f"qr/{target_type}/{target_id}/{token}.png",
            mime_type="image/png",
        )

        # ── Persist QR record ─────────────────────────────────────────────────
        qr_code = QrCode(
            target_type=target_type_enum,
            target_id=target_id,
            url=url,
            image_path=image_path,
            token=token,
            scan_count=0,
            expires_at=expires_at,
            status=QrCodeStatus.ACTIVE,
            created_by=created_by,
        )
        db.session.add(qr_code)
        db.session.commit()

        return qr_code

    # ── Resolution ────────────────────────────────────────────────────────────

    @staticmethod
    def resolve_token(token: str) -> QrCode | None:
        """
        Look up an active, non-expired QR code by token.
        Auto-revokes expired codes on first failed scan.
        Returns None if invalid, revoked, or expired.
        """
        qr_code = QrCode.query.filter_by(token=token, status=QrCodeStatus.ACTIVE).first()

        if qr_code is None:
            return None

        if qr_code.is_expired:
            qr_code.revoke()
            return None

        return qr_code

    # ── Revocation ────────────────────────────────────────────────────────────

    @staticmethod
    def revoke_for_target(target_type: str, target_id) -> int:
        """
        Revoke all active QR codes for a given entity.
        Returns the number of rows updated.
        Called when an itinerary is archived or a booking is cancelled.
        """
        target_type_enum = QrTargetType(target_type)
        count = (
            QrCode.query
            .filter_by(
                target_type=target_type_enum,
                target_id=target_id,
                status=QrCodeStatus.ACTIVE,
            )
            .update({"status": QrCodeStatus.REVOKED}, synchronize_session=False)
        )
        db.session.commit()
        return count

    # ── Data URL helper (kiosk inline display) ────────────────────────────────

    @staticmethod
    def to_data_url(url: str) -> str:
        """
        Generate a base64 PNG data URL for embedding directly in kiosk HTML.
        Avoids a storage round-trip for transient display.
        """
        import base64

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#003366", back_color="#FFFFFF")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"


# Module-level singleton
qr_code_service = QrCodeService()
