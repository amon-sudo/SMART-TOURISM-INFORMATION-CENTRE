"""
Handoff Controller
Three endpoints that together deliver the kiosk-to-phone session transfer.

  POST /api/sessions/<kiosk_session_id>/handoff
      Kiosk calls this when the tourist taps "Continue on phone".
      Body contains the full current session state.
      Returns the QR image (as data URL) and the handoff URL.

  GET  /api/handoff/<token>
      Phone hits this when it scans the QR. No auth required.
      Burns the token, issues a mobile JWT, returns session state.
      Redirects to the mobile deep-link if Accept header prefers HTML
      (i.e. phone browser scanning rather than the app).

  GET  /api/sessions/<kiosk_session_id>/handoff-status
      Kiosk polls this (every 2 seconds) to know when the phone has scanned.
      Returns { transferred: bool, status: str, used_at: str|null }
"""

from __future__ import annotations

from flask               import request, jsonify, redirect, abort
from marshmallow import ValidationError
from flask_jwt_extended  import jwt_required

from app.qr_code.MVC_architecture.services.handoff_service  import handoff_service
from app.qr_code.validators.handoff_schemas import HandoffCreateSchema
from app.utils.responses import ApiResponse


# Helper functions
def success(data=None, message="Success"):
    return ApiResponse.success(data=data, message=message, status_code=200)

def created(data=None, message="Created"):
    return ApiResponse.success(data=data, message=message, status_code=201)

def bad_request(message="Bad request"):
    return ApiResponse.error(message=message, status_code=400)


_create_schema = HandoffCreateSchema()


# ─── 1. Create handoff (kiosk calls this) ─────────────────────────────────────

@jwt_required()
def create_handoff(kiosk_session_id: str):
    """
    POST /api/sessions/<kiosk_session_id>/handoff

    Body:
    {
      "session_state": {
        "step":            "itinerary_review",
        "destination":     "Nairobi",
        "language":        "en",
        "duration_days":   5,
        "interests":       ["wildlife", "museum"],
        "budget_level":    "medium",
        "pace":            "moderate",
        "itinerary_draft": { ... },
        "kiosk_id":        "<uuid>"
      }
    }

    Response:
    {
      "handoff_url":   "https://tourism.go.ke/api/handoff/<token>",
      "qr_data_url":   "data:image/png;base64,...",   ← embed directly in kiosk HTML
      "expires_in":    300,                            ← seconds (5 minutes)
      "token_id":      "<uuid>",
      "status":        "pending"
    }
    """
    try:
        data = _create_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return bad_request({"validation_errors": err.messages})

    try:
        handoff = handoff_service.create_handoff(
            kiosk_session_id=kiosk_session_id,
            session_state=data["session_state"],
        )
    except Exception as e:
        return bad_request(str(e))

    # Generate inline data URL for the kiosk screen
    qr_data_url = handoff_service.to_data_url(handoff.transfer_url)

    return created({
        "handoff_url": handoff.transfer_url,
        "qr_data_url": qr_data_url,
        "expires_in":  300,   # 5 minutes in seconds
        "token_id":    str(handoff.id),
        "status":      handoff.status.value,
    })


# ─── 2. Redeem handoff (phone scans QR — no auth) ────────────────────────────

def redeem_handoff(token: str):
    """
    GET /api/handoff/<token>

    No authentication required — the one-time token IS the credential.
    The phone may hit this from:
      (a) The tourism mobile app  → return JSON with mobile_jwt + session_state
      (b) A phone browser         → redirect to mobile deep-link or web fallback

    Response (JSON — for mobile app):
    {
      "mobile_jwt":        "<jwt>",
      "jwt_expires_in":    900,
      "kiosk_session_id":  "<uuid>",
      "session_state":     { ... },
      "resume_url":        "tourism-app://resume?session=<uuid>",
      "web_resume_url":    "https://tourism.go.ke/mobile/resume/<uuid>"
    }
    """
    mobile_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    try:
        result = handoff_service.redeem_handoff(
            token=token,
            mobile_ip=mobile_ip,
        )
    except ValueError as e:
        # Token invalid / already used / expired
        # Check if phone browser → redirect to friendly error page
        if _prefers_html():
            return redirect(
                f"{_base_url()}/handoff-error?reason={str(e)}", code=302
            )
        return bad_request(str(e))

    # Phone browser (not the app) → redirect to deep-link / web fallback
    if _prefers_html():
        return redirect(result["resume_url"], code=302)

    # Mobile app → return full JSON payload
    return success(result)


# ─── 3. Handoff status (kiosk polls this) ────────────────────────────────────

@jwt_required()
def handoff_status(kiosk_session_id: str):
    """
    GET /api/sessions/<kiosk_session_id>/handoff-status

    Kiosk calls this every 2 seconds while showing the QR on screen.
    When transferred=True the kiosk shows "Session sent to your phone ✓"
    and optionally clears the screen or starts a new session.

    Response:
    {
      "transferred": false,
      "status":      "pending",
      "used_at":     null
    }

    or once scanned:
    {
      "transferred": true,
      "status":      "redeemed",
      "used_at":     "2024-06-01T09:15:30Z"
    }
    """
    status = handoff_service.get_handoff_status(kiosk_session_id)
    return success(status)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _prefers_html() -> bool:
    """True when the request Accept header prefers text/html (phone browser)."""
    accept = request.headers.get("Accept", "")
    return "text/html" in accept and "application/json" not in accept


def _base_url() -> str:
    import os
    return os.getenv("APP_BASE_URL", "http://localhost:5000")
