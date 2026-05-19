"""Storage service shim.

Real deployments swap this for an S3 / Google Cloud Storage backend. The
local default stores everything under ./instance/storage/ and returns a
path that the rest of the app treats as opaque — callers don't assume
S3 vs local. Three modules already import this:

  * app.booking_feature.services.qr_code_service
  * app.itinerary_feature.MVC_architecture.services.qr_code_service
  * app.kiosk_feature.kiosk.MVC_architecture.services.kiosk_services

Without this stub those imports raise ModuleNotFoundError.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO


class StorageService:
    """Minimal local-disk storage backend."""

    base_dir = Path(os.getenv("STORAGE_DIR", "instance/storage")).resolve()

    @classmethod
    def upload(cls, buffer: BinaryIO | bytes, filename: str, mime_type: str | None = None) -> str:
        """Persist a file under base_dir/<filename> and return its path.

        Returns the relative storage path; callers should treat it as
        opaque. If the same filename is uploaded twice the previous
        content is overwritten.
        """
        cls.base_dir.mkdir(parents=True, exist_ok=True)
        target = cls.base_dir / filename
        target.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(buffer, "read"):
            data = buffer.read()
            if hasattr(buffer, "seek"):
                try:
                    buffer.seek(0)
                except Exception:
                    pass
        else:
            data = buffer

        if isinstance(data, str):
            data = data.encode("utf-8")

        target.write_bytes(data)
        return str(target.relative_to(cls.base_dir.parent)) if cls.base_dir.parent in target.parents else str(target)

    @classmethod
    def url_for(cls, storage_path: str) -> str:
        """Return a URL the client can use to retrieve the file."""
        return f"/storage/{storage_path}"
