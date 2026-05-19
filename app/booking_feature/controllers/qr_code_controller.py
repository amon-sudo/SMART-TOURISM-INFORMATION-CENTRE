"""
QrCode Controller
Administrative management of QR codes + public scan handler.
"""

from __future__ import annotations

import uuid

from flask              import abort, current_app, redirect, request
from flask_jwt_extended import get_jwt_identity

from app.extensions               import db
from app.models.qr_code           import QrCode, QrCodeStatus, QrTargetType
from app.validators.schemas       import QrCodeSchema, QrCodeListQuerySchema
from app.services.qr_code_service  import qr_code_service
from app.utils.pagination           import paginate_query
from app.utils.api_response         import success, created, bad_request, no_result


_qr_schema        = QrCodeSchema()
_list_query_schema = QrCodeListQuerySchema()


def _current_user_uuid():
    try:
        identity = get_jwt_identity()
    except Exception:
        identity = request.headers.get("X-User-Id")

    if identity in (None, "", "None"):
        identity = "00000000-0000-0000-0000-000000000001"

    if isinstance(identity, uuid.UUID):
        return identity
    return uuid.UUID(str(identity))


# ─── Admin ────────────────────────────────────────────────────────────────────

def list_qr_codes():
    """
    GET /api/admin/qr-codes
    List QR codes with optional filters.
    Query params: target_type, status, target_id, page, per_page
    """
    args  = _list_query_schema.load(request.args)
    query = QrCode.query

    if args.get("target_type"):
        query = query.filter_by(target_type=args["target_type"])
    if args.get("status"):
        query = query.filter_by(status=args["status"])
    if args.get("target_id"):
        query = query.filter_by(target_id=args["target_id"])

    query = query.order_by(QrCode.created_at.desc())

    result = paginate_query(query, args["page"], args["per_page"])
    result["data"] = _qr_schema.dump(result["data"], many=True)
    return success(result)


def show_qr_code(qr_id: str):
    """
    GET /api/admin/qr-codes/<qr_id>
    Retrieve a single QR code record.
    """
    qr = QrCode.query.get_or_404(qr_id, description="QR code not found")
    return success(_qr_schema.dump(qr))


def revoke(qr_id: str):
    """
    POST /api/admin/qr-codes/<qr_id>/revoke
    Revoke an active QR code.
    """
    qr = QrCode.query.get_or_404(qr_id, description="QR code not found")

    if qr.status == QrCodeStatus.REVOKED:
        return no_result("QR code is already revoked")

    qr.revoke()
    return success({
        "data":    _qr_schema.dump(qr),
        "message": "QR code revoked successfully",
    })


def regenerate(qr_id: str):
    """
    POST /api/admin/qr-codes/<qr_id>/regenerate
    Revoke the current code and issue a fresh one for the same entity.
    Useful when a QR image is compromised or a token is exposed.
    """
    user_id  = _current_user_uuid()
    existing = QrCode.query.get_or_404(qr_id, description="QR code not found")

    # Revoke old code first
    existing.revoke()

    # Issue fresh code for the same target
    new_qr = qr_code_service.generate_or_refresh(
        target_type=existing.target_type.value,
        target_id=existing.target_id,
        created_by=user_id,
        force_new=True,
    )

    return created({
        "data":    _qr_schema.dump(new_qr),
        "message": "QR code regenerated; previous code revoked",
    })


# ─── Public scan handler (no auth) ───────────────────────────────────────────

def scan(token: str):
    """
    GET /api/public/qr/<token>/scan
    Central QR scan handler — no authentication required.
    Increments scan_count and redirects to the correct deep-link
    based on target_type.

    Response codes:
        302 – successful scan, redirect to entity page
        404 – token not found or revoked
        410 – code has expired
    """
    qr = qr_code_service.resolve_token(token)

    if qr is None:
        # Check if it exists but is expired/revoked for a more precise error
        raw = QrCode.query.filter_by(token=token).first()
        if raw and raw.is_expired:
            abort(410, description="This QR code has expired")
        abort(404, description="Invalid or revoked QR code")

    # Thread-safe increment via SQL UPDATE
    qr.increment_scan()

    base_url = current_app.config["APP_BASE_URL"]
    deep_link_map = {
        QrTargetType.ITINERARY:     f"{base_url}/itineraries/{qr.target_id}",
        QrTargetType.BOOKING:       f"{base_url}/bookings/{qr.target_id}/voucher",
        QrTargetType.KIOSK_SESSION: f"{base_url}/sessions/{qr.target_id}",
    }

    destination = deep_link_map.get(qr.target_type)
    if not destination:
        abort(500, description="Unresolvable QR target type")

    return redirect(destination, code=302)
