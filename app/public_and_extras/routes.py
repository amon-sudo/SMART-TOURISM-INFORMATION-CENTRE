"""Routes for the P4 endpoint backlog.

Two blueprints:
- public_bp : unauthenticated /api/public/* routes
- extras_bp : missing /api/v1/* routes (register alias, admin user mgmt,
              recommendations, favourites, notifications, tour packages,
              soft-delete user)

Auth is intentionally loose ("optional JWT, fall back to X-User-Id header")
to stay consistent with the rest of this codebase's testing posture.
Tighten the auth before production.
"""

from __future__ import annotations

import math
import secrets
import uuid
from datetime import datetime, date, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    get_jwt_identity,
    verify_jwt_in_request,
    jwt_required,
)
from sqlalchemy import or_, func, and_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.authanduser.services.services import AuthService
from app.authanduser.utils.utils import (
    validate_password_strength,
    verify_password,
)
from app.tourism_amenitties.attractions.models.attraction import Attraction
from app.tourism_amenitties.attractions.models.product_profile import TourismProductProfile
from app.tourism_amenitties.destination.models.destination import Destination
from app.tourism_amenitties.accommodation.models.accommodation import Accommodation
from app.tourism_amenitties.tours.models.tour_package import TourPackage
from app.tourism_amenitties.events.models.event import Event
from app.tourism_amenitties.accommodation.models.accommodation import RoomType
from app.feedback_media.models import EmergencyContact, Review
from app.user_settings.models.models import (
    User,
    UserPreference,
    UserNotification,
    RefreshToken,
)
from app.utils.responses import ApiResponse
from .models import (
    Favourite,
    Notification,
    AnalyticsEvent,
    UserActivity,
    DailyAnalyticsSnapshot,
)


public_bp = Blueprint("public", __name__)
extras_bp = Blueprint("extras", __name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _current_user_id() -> str | None:
    """Resolve the caller's user id from JWT or the X-User-Id fallback."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
    except Exception:
        identity = None
    if not identity:
        identity = request.headers.get("X-User-Id")
    return str(identity) if identity else None


def _require_user_uuid():
    """Return the current user's UUID or None when there's no caller."""
    raw = _current_user_id()
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except (ValueError, TypeError):
        return None


def _is_admin() -> bool:
    """Permissive admin check — JWT claim 'is_admin' OR X-Admin header.

    Wire to the RBAC module in a follow-up; this keeps the routes runnable
    while RBAC plumbing is finished.
    """
    try:
        from flask_jwt_extended import get_jwt
        if get_jwt().get("is_admin"):
            return True
    except Exception:
        pass
    return request.headers.get("X-Admin", "").lower() in {"1", "true", "yes"}


def _paginate(query, default_per_page: int = 10, max_per_page: int = 50):
    page = max(1, request.args.get("page", 1, type=int) or 1)
    per_page = min(
        max_per_page,
        max(1, request.args.get("per_page", default_per_page, type=int) or default_per_page),
    )
    return query.paginate(page=page, per_page=per_page, error_out=False)


def _attraction_summary(attraction: Attraction) -> dict:
    lat = getattr(attraction, "latitude", None)
    lng = getattr(attraction, "longitude", None)
    return {
        "id": str(attraction.id),
        "name": attraction.name,
        "description": attraction.description,
        "category": attraction.category,
        "destination_id": str(attraction.destination_id) if attraction.destination_id else None,
        "avg_rating": attraction.avg_rating or 0,
        "entry_fee": attraction.entry_fee,
        "is_wheelchair_accessible": bool(attraction.is_wheelchair_accessible),
        "status": attraction.status,
        "latitude": lat,
        "longitude": lng,
    }


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _log_activity(user_id, activity_type: str, target_type: str | None = None,
                  target_id=None, metadata: dict | None = None) -> None:
    """Best-effort user activity log. Never raises into the request path."""
    try:
        db.session.add(UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            target_type=target_type,
            target_id=target_id,
            activity_metadata=metadata,
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()


def _log_event(event_type: str, user_id=None, metadata: dict | None = None) -> None:
    """Best-effort anonymous analytics event log."""
    try:
        db.session.add(AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            event_metadata=metadata,
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()


# ═════════════════════════════════════════════════════════════════════════════
#                            PUBLIC ROUTES (STORY000-010)
# ═════════════════════════════════════════════════════════════════════════════

@public_bp.get("/welcome")
def welcome():
    """STORY000 — landing payload for unauthenticated visitors."""
    lang = (request.args.get("lang") or "en").lower()
    # Featured = top 6 approved attractions by rating
    featured = (
        Attraction.query
        .filter(Attraction.status == "approved")
        .order_by(Attraction.avg_rating.desc().nullslast())
        .limit(6)
        .all()
    )
    return jsonify({
        "language": lang,
        "banner_images": [],  # CMS-managed; empty list until content service ships
        "featured_destinations": [_attraction_summary(a) for a in featured],
        "promotional_content": [],
        "cta_links": [
            {"label": "Register", "href": "/api/v1/auth/register"},
            {"label": "Sign In", "href": "/api/v1/auth/login"},
        ],
    }), 200


@public_bp.get("/attractions")
def public_attractions():
    """STORY001 — public, paginated, approved-only attraction listing."""
    category = request.args.get("category")
    search = request.args.get("search")
    min_rating = request.args.get("min_rating", type=float)

    query = Attraction.query.filter(Attraction.status == "approved")
    if category:
        query = query.filter(Attraction.category == category)
    if min_rating is not None:
        query = query.filter(Attraction.avg_rating >= min_rating)
    if search:
        ilike = f"%{search}%"
        query = query.filter(or_(
            Attraction.name.ilike(ilike),
            Attraction.description.ilike(ilike),
        ))

    pagination = _paginate(query)
    return jsonify({
        "data": [_attraction_summary(a) for a in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        },
    }), 200


@public_bp.get("/emergency-contacts")
def public_emergency_contacts():
    """STORY002 — public emergency contact directory, optionally filtered by type."""
    type_filter = request.args.get("type")
    query = EmergencyContact.query
    if type_filter:
        query = query.filter(EmergencyContact.type == type_filter)
    contacts = query.all()
    return jsonify([
        {
            "id": str(c.id),
            "name": c.name,
            "type": c.type,
            "phone": c.phone,
            "tel_uri": f"tel:{c.phone}" if c.phone else None,
            "city": c.city,
            "region": c.region,
        }
        for c in contacts
    ]), 200


@public_bp.get("/search")
def public_search():
    """STORY004 — basic full-text-ish search over approved attractions and destinations."""
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"data": [], "query": q}), 200

    _log_event("search", metadata={"query": q})

    ilike = f"%{q}%"
    attractions = (
        Attraction.query
        .filter(Attraction.status == "approved")
        .filter(or_(Attraction.name.ilike(ilike), Attraction.description.ilike(ilike)))
        .limit(20)
        .all()
    )
    destinations = (
        Destination.query
        .filter(or_(
            Destination.canonical_name.ilike(ilike),
            Destination.slug.ilike(ilike),
        ))
        .limit(20)
        .all()
    )
    return jsonify({
        "query": q,
        "attractions": [_attraction_summary(a) for a in attractions],
        "destinations": [
            {"id": str(d.id), "canonical_name": d.canonical_name, "slug": d.slug}
            for d in destinations
        ],
    }), 200


@public_bp.get("/map")
def public_map():
    """STORY006 — GeoJSON FeatureCollection of approved attractions."""
    attractions = (
        Attraction.query.filter(Attraction.status == "approved").all()
    )
    features = []
    for a in attractions:
        lat = getattr(a, "latitude", None)
        lng = getattr(a, "longitude", None)
        geometry = None
        if lat is not None and lng is not None:
            # GeoJSON expects [lng, lat] ordering.
            geometry = {"type": "Point", "coordinates": [float(lng), float(lat)]}
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "id": str(a.id),
                "name": a.name,
                "category": a.category,
                "rating": a.avg_rating or 0,
            },
        })
    return jsonify({"type": "FeatureCollection", "features": features}), 200


@public_bp.get("/accommodations")
def public_accommodations():
    """STORY007 — public accommodation listing."""
    query = Accommodation.query
    min_rating = request.args.get("min_rating", type=int)
    if min_rating is not None:
        query = query.filter(Accommodation.star_rating >= min_rating)
    pagination = _paginate(query)
    return jsonify({
        "data": [
            {
                "id": str(item.id),
                "attraction_id": str(item.attraction_id),
                "star_rating": item.star_rating,
                "check_in_time": item.check_in_time.isoformat() if item.check_in_time else None,
                "check_out_time": item.check_out_time.isoformat() if item.check_out_time else None,
                "policies": item.policies,
            }
            for item in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        },
    }), 200


@public_bp.get("/destinations/<uuid:destination_id>/info")
def public_destination_info(destination_id):
    """STORY008 — overview / culture / weather / tips for a destination."""
    destination = db.session.get(Destination, destination_id)
    if not destination:
        return jsonify({"error": "Destination not found"}), 404
    lang = (
        (request.args.get("lang") or request.headers.get("Accept-Language") or "en")
        .split(",")[0].strip().lower()
    )

    def _localize(blob):
        """JSON blobs are keyed by locale. Fall back to 'en' or the first key."""
        if not isinstance(blob, dict) or not blob:
            return blob
        return blob.get(lang) or blob.get("en") or next(iter(blob.values()), None)

    return jsonify({
        "id": str(destination.id),
        "language": lang,
        "canonical_name": destination.canonical_name,
        "slug": destination.slug,
        "description": destination.description,
        "is_wheelchair_accessible": bool(getattr(destination, "is_wheelchair_accessible", False)),
        "overview": _localize(getattr(destination, "overview_json", None)),
        "culture": _localize(getattr(destination, "culture_json", None)),
        "weather_info": _localize(getattr(destination, "weather_info", None)),
        "travel_tips": _localize(getattr(destination, "travel_tips_json", None)),
    }), 200


@public_bp.post("/kiosk/session/reset")
def public_kiosk_reset():
    """STORY009 — start a fresh anonymous kiosk session.

    Body (optional):
      { "kiosk_id": "<uuid>" }      // pin the session to a known kiosk
    """
    from app.kiosk_feature.kiosk.MVC_architecture.models.kiosk_session import (
        KioskSession, KioskSessionStatus,
    )
    from app.kiosk_feature.kiosk.MVC_architecture.models.kiosk import Kiosk

    data = request.get_json(silent=True) or {}
    kiosk_uuid = None
    if data.get("kiosk_id"):
        try:
            kiosk_uuid = uuid.UUID(str(data["kiosk_id"]))
        except (ValueError, TypeError):
            return jsonify({"error": "kiosk_id must be a valid UUID"}), 400
        if not db.session.get(Kiosk, kiosk_uuid):
            return jsonify({"error": "Kiosk not found"}), 404

    if kiosk_uuid is None:
        # No kiosk specified — emit an opaque anonymous token so non-kiosk
        # callers (web warmup, integration tests) still get a usable response.
        token = secrets.token_urlsafe(32)
        _log_event("kiosk_session_reset_anonymous", metadata={"token_prefix": token[:8]})
        return jsonify({
            "session_token": token,
            "kiosk_id": None,
            "issued_at": datetime.utcnow().isoformat() + "Z",
            "idle_timeout_seconds": 180,
            "persisted": False,
        }), 201

    session = KioskSession(
        kiosk_id=kiosk_uuid,
        session_token=secrets.token_urlsafe(32),
        status=KioskSessionStatus.ACTIVE if hasattr(KioskSessionStatus, "ACTIVE") else list(KioskSessionStatus)[0],
        started_at=datetime.utcnow(),
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        state={},
    )
    db.session.add(session)
    db.session.commit()
    _log_event("kiosk_session_started", metadata={"session_id": str(session.id)})

    return jsonify({
        "session_id": str(session.id),
        "session_token": session.session_token,
        "kiosk_id": str(session.kiosk_id),
        "issued_at": session.started_at.isoformat() + "Z",
        "idle_timeout_seconds": 180,
        "persisted": True,
    }), 201


@public_bp.post("/session/qr")
def public_session_qr():
    """STORY003 — generate a phone-handoff QR for an existing kiosk session.

    Body:
      { "kiosk_session_id": "<uuid>" }

    On success returns the same shape as /api/v1/sessions/<id>/handoff so
    public kiosk frontends can hit either endpoint.
    """
    from app.kiosk_feature.kiosk.MVC_architecture.services.kiosk_services import transfer_service
    from app.kiosk_feature.kiosk.MVC_architecture.models.kiosk_session import KioskSession

    data = request.get_json(silent=True) or {}
    raw = data.get("kiosk_session_id")
    if not raw:
        return jsonify({"error": "kiosk_session_id required"}), 400
    try:
        session_uuid = uuid.UUID(str(raw))
    except (ValueError, TypeError):
        return jsonify({"error": "kiosk_session_id must be a valid UUID"}), 400
    if not db.session.get(KioskSession, session_uuid):
        return jsonify({"error": "Kiosk session not found"}), 404

    try:
        transfer = transfer_service.create_transfer(session_uuid)
    except Exception as exc:
        return jsonify({"error": "Failed to create transfer", "detail": str(exc)}), 500

    return jsonify({
        "transfer_id": str(transfer.id),
        "kiosk_session_id": str(transfer.kiosk_session_id),
        "token": transfer.token,
        "transfer_url": transfer.transfer_url,
        "qr_image_path": transfer.qr_image_path,
        "expires_at": transfer.expires_at.isoformat() if transfer.expires_at else None,
        "status": transfer.status.value if hasattr(transfer.status, "value") else str(transfer.status),
    }), 201


# ═════════════════════════════════════════════════════════════════════════════
#                           EXTRAS — /api/v1/* gaps
# ═════════════════════════════════════════════════════════════════════════════

# ── Auth alias /register → /signup ───────────────────────────────────────────

@extras_bp.post("/auth/register")
def auth_register_alias():
    """STORY011 — /auth/register alias around AuthService.signup."""
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")
    if not email or not password:
        return ApiResponse.error(
            message="Email and password required",
            code="MISSING_DATA",
            status_code=400,
        )
    pw_errors = validate_password_strength(password)
    if pw_errors:
        return ApiResponse.error(
            message="Password does not meet strength requirements",
            code="WEAK_PASSWORD",
            status_code=422,
            details={"password": pw_errors},
        )
    user = AuthService.signup(email, password, username=username)
    if not user:
        return ApiResponse.error(
            message="Email already registered",
            code="CONFLICT",
            status_code=409,
        )
    tokens = AuthService.generate_tokens(str(user.id))
    return jsonify({
        "message": "Account created",
        "user_id": str(user.id),
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }), 201


# ── DELETE /api/v1/users/<id> (STORY016) ─────────────────────────────────────

@extras_bp.delete("/users/<uuid:user_id>")
@jwt_required()
def soft_delete_user(user_id):
    """STORY016 — owner-confirmed soft delete with password challenge."""
    caller_uuid = _require_user_uuid()
    if caller_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401
    if str(caller_uuid) != str(user_id):
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    password = data.get("password")
    if not password:
        return jsonify({"error": "password required"}), 400

    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        # Generic response to avoid leaking account state.
        return jsonify({"message": "Account scheduled for deletion"}), 200
    if not verify_password(user.password_hash, password):
        return jsonify({"error": "Incorrect password"}), 401

    # Soft-delete + anonymise + revoke all sessions.
    user.is_active = False
    user.deleted_at = datetime.utcnow()
    user.email = f"deleted_{user.id}@anon.local"
    user.username = None
    RefreshToken.query.filter_by(user_id=user.id, revoked=False).update(
        {"revoked": True}
    )
    db.session.commit()
    return jsonify({"message": "Account scheduled for deletion"}), 200


# ── Admin user management (STORY020) ─────────────────────────────────────────

@extras_bp.get("/admin/users")
@jwt_required()
def admin_list_users():
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    search = request.args.get("search")
    query = User.query
    if search:
        ilike = f"%{search}%"
        query = query.filter(or_(User.email.ilike(ilike), User.username.ilike(ilike)))
    pagination = _paginate(query, default_per_page=20)
    return jsonify({
        "data": [
            {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "is_active": u.is_active,
                "deleted_at": u.deleted_at.isoformat() if u.deleted_at else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        },
    }), 200


@extras_bp.patch("/admin/users/<uuid:user_id>")
@jwt_required()
def admin_update_user(user_id):
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json() or {}
    status = data.get("status")
    if status not in {None, "active", "suspended"}:
        return jsonify({"error": "status must be 'active' or 'suspended'"}), 400
    if status == "suspended":
        user.is_active = False
        RefreshToken.query.filter_by(user_id=user.id, revoked=False).update(
            {"revoked": True}
        )
    elif status == "active":
        user.is_active = True
    db.session.commit()
    return jsonify({
        "id": str(user.id),
        "is_active": user.is_active,
        "status": "active" if user.is_active else "suspended",
        "reason": data.get("reason"),
    }), 200


# ── Recommendations (STORY025) ───────────────────────────────────────────────

@extras_bp.get("/recommendations")
@jwt_required()
def recommendations():
    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401
    prefs = UserPreference.query.filter_by(user_id=user_uuid).first()
    if not prefs:
        return jsonify({
            "error": "Preferences must be set before fetching recommendations"
        }), 400

    query = Attraction.query.filter(Attraction.status == "approved")
    interests = prefs.interests or []
    if isinstance(interests, list) and interests:
        query = query.filter(Attraction.category.in_(interests))
    # Crude scoring: avg_rating descending, then alphabetical.
    attractions = query.order_by(
        Attraction.avg_rating.desc().nullslast(), Attraction.name
    ).limit(20).all()
    return jsonify({
        "preferences": {
            "interests": interests,
            "budget_level": prefs.budget_level,
            "pace": prefs.pace,
            "stay_duration_days": prefs.stay_duration_days,
        },
        "recommendations": [_attraction_summary(a) for a in attractions],
    }), 200


# ── Favourites (STORY044) ────────────────────────────────────────────────────

@extras_bp.get("/favourites")
@jwt_required()
def list_favourites():
    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401
    favs = (
        Favourite.query
        .filter_by(user_id=user_uuid)
        .order_by(Favourite.created_at.desc())
        .all()
    )
    return jsonify({"data": [f.to_dict() for f in favs]}), 200


@extras_bp.post("/favourites")
@jwt_required()
def add_favourite():
    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json() or {}
    attraction_raw = data.get("attraction_id")
    if not attraction_raw:
        return jsonify({"error": "attraction_id required"}), 400
    try:
        attraction_uuid = uuid.UUID(str(attraction_raw))
    except (ValueError, TypeError):
        return jsonify({"error": "attraction_id must be a valid UUID"}), 400
    if not db.session.get(Attraction, attraction_uuid):
        return jsonify({"error": "Attraction not found"}), 404
    try:
        fav = Favourite(user_id=user_uuid, attraction_id=attraction_uuid)
        db.session.add(fav)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Already in favourites"}), 409
    _log_activity(user_uuid, "favourite_added", "attraction", attraction_uuid)
    return jsonify(fav.to_dict()), 201


@extras_bp.delete("/favourites/<uuid:attraction_id>")
@jwt_required()
def remove_favourite(attraction_id):
    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401
    fav = Favourite.query.filter_by(
        user_id=user_uuid, attraction_id=attraction_id
    ).first()
    if not fav:
        return jsonify({"error": "Favourite not found"}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "Removed from favourites"}), 200


# ── Notifications (STORY039) ─────────────────────────────────────────────────

@extras_bp.get("/notifications")
@jwt_required()
def list_notifications():
    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401
    only_unread = request.args.get("unread") == "true"
    query = Notification.query.filter_by(user_id=user_uuid)
    if only_unread:
        query = query.filter_by(is_read=False)
    query = query.order_by(Notification.created_at.desc())
    pagination = _paginate(query, default_per_page=20)
    return jsonify({
        "data": [n.to_dict() for n in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        },
    }), 200


@extras_bp.patch("/notifications/<uuid:notification_id>/read")
@jwt_required()
def mark_notification_read(notification_id):
    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401
    notif = Notification.query.filter_by(
        id=notification_id, user_id=user_uuid
    ).first()
    if not notif:
        return jsonify({"error": "Notification not found"}), 404
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.utcnow()
        db.session.commit()
    return jsonify(notif.to_dict()), 200


# ── Tour packages (STORY035) ─────────────────────────────────────────────────

@extras_bp.get("/tour-packages")
def list_tour_packages():
    """Public-friendly listing of active tour packages."""
    query = TourPackage.query.filter(TourPackage.status == "active")
    pagination = _paginate(query)
    return jsonify({
        "data": [
            {
                "id": str(tp.id),
                "operator_id": str(tp.operator_id),
                "name": tp.name,
                "description": tp.description,
                "duration_days": tp.duration_days,
                "price": tp.price,
                "max_participants": tp.max_participants,
                "status": tp.status,
            }
            for tp in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        },
    }), 200


@extras_bp.get("/tour-packages/<uuid:package_id>")
def show_tour_package(package_id):
    tp = db.session.get(TourPackage, package_id)
    if not tp or tp.status != "active":
        return jsonify({"error": "Tour package not found"}), 404
    return jsonify({
        "id": str(tp.id),
        "operator_id": str(tp.operator_id),
        "name": tp.name,
        "description": tp.description,
        "duration_days": tp.duration_days,
        "price": tp.price,
        "max_participants": tp.max_participants,
        "status": tp.status,
    }), 200


# ── Tour booking (STORY035 — POST /api/v1/bookings/tour) ─────────────────────

@extras_bp.post("/bookings/tour")
@jwt_required()
def book_tour():
    """STORY035 — dedicated entry point for tour-package bookings.

    Thin wrapper that constructs a Booking with type='tour' and a single
    BookingItem targeting the chosen tour_package. Real payment processing
    is delegated to the existing /api/v1/payments/* endpoints; clients
    quote payment_intent_id after this returns 201.
    """
    from app.booking_feature.models.booking import (
        Booking, BookingItem, BookingStatus, BookingType, BookingItemTargetType, RefundStatus
    )
    from app.services.reference_service import ReferenceService

    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    package_raw = data.get("package_id")
    participants = int(data.get("participants", 1) or 1)
    if not package_raw:
        return jsonify({"error": "package_id required"}), 400
    if participants < 1:
        return jsonify({"error": "participants must be >= 1"}), 400

    try:
        package_uuid = uuid.UUID(str(package_raw))
    except (ValueError, TypeError):
        return jsonify({"error": "package_id must be a valid UUID"}), 400

    pkg = db.session.get(TourPackage, package_uuid)
    if not pkg or pkg.status != "active":
        return jsonify({"error": "Tour package not found"}), 404
    if pkg.max_participants and participants > pkg.max_participants:
        return jsonify({
            "error": f"Max {pkg.max_participants} participants per booking"
        }), 400

    total_cost = float(pkg.price or 0) * participants

    try:
        booking = Booking(
            user_id=user_uuid,
            reference_number=ReferenceService.generate("TR"),
            type=BookingType.TOUR,
            status=BookingStatus.PENDING,
            total_cost=total_cost,
            refund_status=RefundStatus.NONE,
        )
        db.session.add(booking)
        db.session.flush()
        db.session.add(BookingItem(
            booking_id=booking.id,
            target_type=BookingItemTargetType.TOUR_PACKAGE,
            target_id=package_uuid,
            quantity=participants,
            price_at_booking=float(pkg.price or 0),
            notes=data.get("notes"),
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    _log_activity(user_uuid, "tour_booking_created", "booking", booking.id,
                  {"package_id": str(package_uuid), "participants": participants})

    return jsonify({
        "id": str(booking.id),
        "reference_number": booking.reference_number,
        "status": booking.status.value,
        "type": booking.type.value,
        "total_cost": booking.total_cost,
        "package_id": str(package_uuid),
        "participants": participants,
    }), 201


# ── Notification preferences (STORY039) ──────────────────────────────────────

@extras_bp.get("/users/<uuid:user_id>/notification-preferences")
@jwt_required()
def get_notification_prefs(user_id):
    caller = _require_user_uuid()
    if caller is None:
        return jsonify({"error": "Unauthorized"}), 401
    if str(caller) != str(user_id) and not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    prefs = UserNotification.query.filter_by(user_id=user_id).first()
    if not prefs:
        # Return defaults if the user has never persisted preferences.
        return jsonify({
            "email_alerts": True,
            "push_notifications": True,
            "sms_enabled": False,
            "marketing_emails_enabled": False,
            "security_alerts_enabled": True,
            "booking_updates_enabled": True,
        }), 200
    return jsonify({
        "email_alerts": prefs.email_alerts,
        "push_notifications": prefs.push_notifications,
        "email_enabled": prefs.email_enabled,
        "push_enabled": prefs.push_enabled,
        "sms_enabled": prefs.sms_enabled,
        "marketing_emails_enabled": prefs.marketing_emails_enabled,
        "security_alerts_enabled": prefs.security_alerts_enabled,
        "booking_updates_enabled": prefs.booking_updates_enabled,
    }), 200


@extras_bp.patch("/users/<uuid:user_id>/notification-preferences")
@jwt_required()
def update_notification_prefs(user_id):
    caller = _require_user_uuid()
    if caller is None:
        return jsonify({"error": "Unauthorized"}), 401
    if str(caller) != str(user_id) and not _is_admin():
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    prefs = UserNotification.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = UserNotification(user_id=user_id)
        db.session.add(prefs)

    allowed = {
        "email_alerts", "push_notifications", "email_enabled", "push_enabled",
        "sms_enabled", "marketing_emails_enabled",
        "security_alerts_enabled", "booking_updates_enabled",
    }
    for field in allowed:
        if field in data:
            setattr(prefs, field, bool(data[field]))
    db.session.commit()
    return jsonify({field: getattr(prefs, field) for field in allowed}), 200


# ── User profile aliases (STORY015 — /api/v1/users/<id>) ─────────────────────

def _profile_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "profile": ({
            "full_name": user.profile.full_name,
            "bio": user.profile.bio,
            "profile_picture": user.profile.profile_picture,
            "language_preference": user.profile.language_preference,
            "currency_preference": user.profile.currency_preference,
            "timezone": user.profile.timezone,
            "last_login_at": user.profile.last_login_at.isoformat() if user.profile and user.profile.last_login_at else None,
        } if getattr(user, "profile", None) else None),
    }


@extras_bp.get("/users/<uuid:user_id>")
@jwt_required()
def get_user_profile(user_id):
    """STORY015 — GET /api/v1/users/{id}. Mirrors GET /api/v1/settings."""
    caller = _require_user_uuid()
    if caller is None:
        return jsonify({"error": "Unauthorized"}), 401
    if str(caller) != str(user_id) and not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        return jsonify({"error": "User not found"}), 404
    return jsonify(_profile_payload(user)), 200


@extras_bp.patch("/users/<uuid:user_id>")
@jwt_required()
def patch_user_profile(user_id):
    """STORY015 — PATCH /api/v1/users/{id}. Updates email/username + profile."""
    from app.user_settings.models.models import UserProfile

    caller = _require_user_uuid()
    if caller is None:
        return jsonify({"error": "Unauthorized"}), 401
    if str(caller) != str(user_id) and not _is_admin():
        return jsonify({"error": "Forbidden"}), 403

    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    if "email" in data and data["email"] != user.email:
        existing = User.query.filter(User.email == data["email"], User.id != user.id).first()
        if existing:
            return jsonify({"error": "Email already in use"}), 409
        user.email = data["email"]
    if "username" in data:
        user.username = data["username"]

    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        user.profile = profile

    for field in ("full_name", "bio", "profile_picture", "language_preference",
                  "currency_preference", "timezone"):
        if field in data:
            setattr(profile, field, data[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already in use"}), 409

    _log_activity(user.id, "profile_updated", "user", user.id,
                  {"fields": list(data.keys())})

    return jsonify(_profile_payload(user)), 200


# ── Admin: review moderation (STORY022) ──────────────────────────────────────

@extras_bp.patch("/admin/reviews/<uuid:review_id>")
@jwt_required()
def admin_moderate_review(review_id):
    """Flag / hide / approve / respond. Body keys: status, admin_response."""
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    review = db.session.get(Review, review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status not in {None, "approved", "rejected", "flagged", "hidden", "pending"}:
        return jsonify({
            "error": "status must be one of approved/rejected/flagged/hidden/pending"
        }), 400
    if new_status:
        review.status = new_status
    db.session.commit()
    return jsonify({
        "id": str(review.id),
        "status": review.status,
        "admin_response": data.get("admin_response"),
    }), 200


# ── Admin analytics (STORY023) ───────────────────────────────────────────────

@extras_bp.get("/admin/analytics")
@jwt_required()
def admin_analytics():
    """Roll-up metrics for the admin dashboard.

    Query params:
      from=YYYY-MM-DD, to=YYYY-MM-DD   defaults to the last 30 days.

    Returns live aggregates of the canonical entities plus the latest
    daily snapshot. The pre-computed snapshot table is used when present;
    everything else is computed on-the-fly for responsiveness.
    """
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403

    today = date.today()
    try:
        d_from = (
            datetime.strptime(request.args["from"], "%Y-%m-%d").date()
            if "from" in request.args else today - timedelta(days=30)
        )
        d_to = (
            datetime.strptime(request.args["to"], "%Y-%m-%d").date()
            if "to" in request.args else today
        )
    except ValueError:
        return jsonify({"error": "Invalid date format; use YYYY-MM-DD"}), 400

    from app.booking_feature.models.booking import Booking, BookingStatus

    bookings_total = db.session.query(func.count(Booking.id)).filter(
        Booking.created_at >= d_from, Booking.created_at < d_to + timedelta(days=1)
    ).scalar() or 0
    bookings_confirmed = db.session.query(func.count(Booking.id)).filter(
        Booking.created_at >= d_from, Booking.created_at < d_to + timedelta(days=1),
        Booking.status == BookingStatus.CONFIRMED,
    ).scalar() or 0
    users_active = db.session.query(func.count(func.distinct(AnalyticsEvent.user_id))).filter(
        AnalyticsEvent.user_id.is_not(None),
        AnalyticsEvent.created_at >= d_from,
        AnalyticsEvent.created_at < d_to + timedelta(days=1),
    ).scalar() or 0
    events_total = db.session.query(func.count(AnalyticsEvent.id)).filter(
        AnalyticsEvent.created_at >= d_from,
        AnalyticsEvent.created_at < d_to + timedelta(days=1),
    ).scalar() or 0
    top_attractions = (
        db.session.query(Attraction.id, Attraction.name, Attraction.view_count)
        .filter(Attraction.status == "approved")
        .order_by(Attraction.view_count.desc().nullslast())
        .limit(10).all()
    )
    top_searches = (
        db.session.query(
            AnalyticsEvent.event_metadata,
            func.count(AnalyticsEvent.id).label("n"),
        )
        .filter(AnalyticsEvent.event_type == "search",
                AnalyticsEvent.created_at >= d_from,
                AnalyticsEvent.created_at < d_to + timedelta(days=1))
        .group_by(AnalyticsEvent.event_metadata)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(10).all()
    )
    booking_conversion = (
        (bookings_confirmed / bookings_total) if bookings_total else 0.0
    )

    latest_snapshot = (
        DailyAnalyticsSnapshot.query
        .order_by(DailyAnalyticsSnapshot.date.desc())
        .first()
    )

    return jsonify({
        "date_range": {"from": d_from.isoformat(), "to": d_to.isoformat()},
        "bookings_total": bookings_total,
        "bookings_confirmed": bookings_confirmed,
        "booking_conversion_rate": round(booking_conversion, 4),
        "users_active": users_active,
        "events_total": events_total,
        "top_attractions": [
            {"id": str(a.id), "name": a.name, "view_count": a.view_count or 0}
            for a in top_attractions
        ],
        "top_searches": [
            {"query": (md or {}).get("query") if isinstance(md, dict) else None, "count": n}
            for md, n in top_searches
        ],
        "latest_snapshot": latest_snapshot.to_dict() if latest_snapshot else None,
    }), 200


@extras_bp.post("/admin/analytics/snapshot")
@jwt_required()
def admin_compute_snapshot():
    """Compute (and upsert) a DailyAnalyticsSnapshot for ?date=YYYY-MM-DD
    (defaults to today). Idempotent.
    """
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403

    try:
        target = (
            datetime.strptime(request.args["date"], "%Y-%m-%d").date()
            if "date" in request.args else date.today()
        )
    except ValueError:
        return jsonify({"error": "Invalid date; use YYYY-MM-DD"}), 400

    from app.booking_feature.models.booking import Booking

    next_day = target + timedelta(days=1)
    sessions = db.session.query(func.count(AnalyticsEvent.id)).filter(
        AnalyticsEvent.event_type == "session_start",
        AnalyticsEvent.created_at >= target,
        AnalyticsEvent.created_at < next_day,
    ).scalar() or 0
    bookings = db.session.query(func.count(Booking.id)).filter(
        Booking.created_at >= target,
        Booking.created_at < next_day,
    ).scalar() or 0
    users_active = db.session.query(func.count(func.distinct(AnalyticsEvent.user_id))).filter(
        AnalyticsEvent.user_id.is_not(None),
        AnalyticsEvent.created_at >= target,
        AnalyticsEvent.created_at < next_day,
    ).scalar() or 0
    avg_rating = db.session.query(func.coalesce(func.avg(Review.rating), 0)).scalar() or 0

    snap = DailyAnalyticsSnapshot.query.filter_by(date=target).first()
    if snap is None:
        snap = DailyAnalyticsSnapshot(date=target)
        db.session.add(snap)
    snap.total_sessions = int(sessions)
    snap.total_bookings = int(bookings)
    snap.total_users_active = int(users_active)
    snap.avg_rating = float(avg_rating)
    snap.booking_conversion_rate = (bookings / sessions) if sessions else 0.0
    db.session.commit()

    return jsonify(snap.to_dict()), 200


# ── Navigation routing (STORY036) ────────────────────────────────────────────

@extras_bp.get("/navigation/route")
def navigation_route():
    """STORY036 — directions between two coordinates.

    Query params: from_lat, from_lng, to_lat, to_lng, mode=(walking|driving)

    Returns GeoJSON LineString of the straight-line path plus estimated
    distance + travel time using a haversine + per-mode speed assumption.
    Production deployments should swap this for a real routing engine
    (OSRM / Mapbox / Google Directions) by replacing the function body.
    """
    try:
        f_lat = float(request.args["from_lat"])
        f_lng = float(request.args["from_lng"])
        t_lat = float(request.args["to_lat"])
        t_lng = float(request.args["to_lng"])
    except (KeyError, TypeError, ValueError):
        return jsonify({
            "error": "from_lat, from_lng, to_lat, to_lng required (floats)"
        }), 400

    mode = (request.args.get("mode") or "driving").lower()
    if mode not in {"walking", "driving"}:
        return jsonify({"error": "mode must be 'walking' or 'driving'"}), 400

    distance_km = _haversine_km(f_lat, f_lng, t_lat, t_lng)
    speed_kph = 5.0 if mode == "walking" else 40.0
    duration_minutes = (distance_km / speed_kph) * 60

    geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[f_lng, f_lat], [t_lng, t_lat]],
        },
        "properties": {
            "mode": mode,
            "distance_km": round(distance_km, 3),
            "duration_minutes": round(duration_minutes, 1),
            "engine": "haversine-stub",
        },
    }
    steps = [
        {"instruction": f"Head toward destination ({t_lat:.4f}, {t_lng:.4f})",
         "distance_km": round(distance_km, 3)},
        {"instruction": "Arrive at destination"},
    ]
    return jsonify({"route": geojson, "steps": steps}), 200


# ── Events (ERD events table) ────────────────────────────────────────────────

@extras_bp.get("/events")
def list_events():
    """Public listing of tourism events."""
    query = Event.query
    pagination = _paginate(query)
    return jsonify({
        "data": [
            {
                "id": str(e.id),
                "name": getattr(e, "name", None),
                "description": getattr(e, "description", None),
                "destination_id": str(e.destination_id) if getattr(e, "destination_id", None) else None,
                "attraction_id": str(e.attraction_id) if getattr(e, "attraction_id", None) else None,
            }
            for e in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        },
    }), 200


@extras_bp.get("/events/<uuid:event_id>")
def show_event(event_id):
    e = db.session.get(Event, event_id)
    if not e:
        return jsonify({"error": "Event not found"}), 404
    return jsonify({
        "id": str(e.id),
        "name": getattr(e, "name", None),
        "description": getattr(e, "description", None),
        "destination_id": str(e.destination_id) if getattr(e, "destination_id", None) else None,
        "attraction_id": str(e.attraction_id) if getattr(e, "attraction_id", None) else None,
    }), 200


# ── Room types (ERD room_types table) ────────────────────────────────────────

@extras_bp.get("/accommodations/<uuid:accommodation_id>/rooms")
def list_room_types(accommodation_id):
    rooms = RoomType.query.filter_by(accommodation_id=accommodation_id).all()
    return jsonify([
        {
            "id": str(r.id),
            "accommodation_id": str(r.accommodation_id),
            "name": r.name,
            "base_price": r.base_price,
            "capacity": r.capacity,
            "amenities_json": r.amenities_json,
        }
        for r in rooms
    ]), 200


# ── User activity log (ERD user_activities) ──────────────────────────────────

@extras_bp.get("/users/<uuid:user_id>/activity")
@jwt_required()
def user_activity_log(user_id):
    caller = _require_user_uuid()
    if caller is None:
        return jsonify({"error": "Unauthorized"}), 401
    if str(caller) != str(user_id) and not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    query = UserActivity.query.filter_by(user_id=user_id).order_by(
        UserActivity.created_at.desc()
    )
    pagination = _paginate(query, default_per_page=20)
    return jsonify({
        "data": [a.to_dict() for a in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
        },
    }), 200


# ── Tourism Product Profile (Kenya Ministry of Tourism form) ────────────────
# Implements the full TOURISM PRODUCTS PROFILE the client provided. The model
# already lives at app/tourism_amenitties/attractions/models/product_profile.py;
# these routes expose CRUD over it.
#
# The form's Section 1 (Name + Type/Category) lives on the parent Attraction.
# Sections 2-7 are in the TourismProductProfile row (1:1 with Attraction.id).

# Vocabulary from the form's Section 1.1 — used to validate Attraction.category
# when callers want strict validation. Public endpoints don't enforce it (some
# existing rows may use other values); admin POST/PATCH should opt in via the
# strict_category=true query param.
KENYA_TOURISM_CATEGORIES = {
    "cultural_and_heritage",
    "adventure",
    "beach",
    "sports",
    "agro",
    "gastronomy",
    "avi_tourism",
    "health_and_wellness",
    "ecotourism",
    "astral",
}

# Sub-keys allowed inside the JSON infrastructure_status blob.
INFRASTRUCTURE_KEYS = {
    "roads",                  # 4.1 Roads (access & condition)
    "visitor_center",         # 4.2 Visitor Center / Information Kiosks
    "fencing_security",       # 4.3 Fencing & Security
    "water_supply",           # 4.4
    "signage",                # 4.5 Signage & Interpretation
    "parking",                # 4.6
    "rest_areas",             # 4.7 Rest Areas / Toilets
}

# Vocabulary for Section 4.8 site_status
SITE_STATUSES = {"under_development", "active", "seasonal", "decommissioned"}


def _profile_to_dict(profile: TourismProductProfile) -> dict:
    return {
        "id": str(profile.id),
        "attraction_id": str(profile.attraction_id),
        # Section 2 — Location
        "county": profile.county,
        "sub_county": profile.sub_county,
        "ward": profile.ward,
        "locality": profile.locality,
        "gps_coordinates": profile.gps_coordinates,
        # Section 3 — Features
        "unique_features": profile.unique_features,
        "conservation_efforts": profile.conservation_efforts,
        "visitor_capacity": profile.visitor_capacity,
        "experience_types": profile.experience_types,
        "average_stay_time": profile.average_stay_time,
        "best_visiting_period": profile.best_visiting_period,
        "key_events": profile.key_events,
        # Section 4 — Situational Analysis
        "infrastructure_status": profile.infrastructure_status,
        "site_status": profile.site_status,
        # Section 5 — Associated Services
        "tour_operators": profile.tour_operators,
        "nearby_accommodation": profile.nearby_accommodation,
        "local_guides": profile.local_guides,
        "distance_to_hub": profile.distance_to_hub,
        # Section 6 — Community
        "community_role": profile.community_role,
        "community_benefits": profile.community_benefits,
        "community_enterprises": profile.community_enterprises,
        # Section 7 — Recommendations
        "competitiveness_assessment": profile.competitiveness_assessment,
        "infrastructure_gaps": profile.infrastructure_gaps,
        "sustainability_strategies": profile.sustainability_strategies,
        "growth_opportunities": profile.growth_opportunities,
        "community_empowerment": profile.community_empowerment,
        "other_observations": profile.other_observations,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


_PROFILE_WRITABLE_FIELDS = {
    "county", "sub_county", "ward", "locality", "gps_coordinates",
    "unique_features", "conservation_efforts", "visitor_capacity",
    "experience_types", "average_stay_time", "best_visiting_period", "key_events",
    "infrastructure_status", "site_status",
    "tour_operators", "nearby_accommodation", "local_guides", "distance_to_hub",
    "community_role", "community_benefits", "community_enterprises",
    "competitiveness_assessment", "infrastructure_gaps", "sustainability_strategies",
    "growth_opportunities", "community_empowerment", "other_observations",
}


def _apply_profile_payload(profile: TourismProductProfile, data: dict) -> tuple[bool, str | None]:
    """Apply a (validated) payload onto the profile. Returns (ok, error_msg)."""
    if "site_status" in data and data["site_status"] not in (None, "", *SITE_STATUSES):
        return False, f"site_status must be one of {sorted(SITE_STATUSES)}"
    if "infrastructure_status" in data and data["infrastructure_status"] is not None:
        infra = data["infrastructure_status"]
        if not isinstance(infra, dict):
            return False, "infrastructure_status must be an object"
        unknown = set(infra) - INFRASTRUCTURE_KEYS
        if unknown:
            return False, f"unknown infrastructure_status keys: {sorted(unknown)}"
    if "visitor_capacity" in data and data["visitor_capacity"] is not None:
        try:
            data["visitor_capacity"] = int(data["visitor_capacity"])
        except (TypeError, ValueError):
            return False, "visitor_capacity must be an integer"
    for field in _PROFILE_WRITABLE_FIELDS:
        if field in data:
            setattr(profile, field, data[field])
    return True, None


@extras_bp.get("/attractions/<uuid:attraction_id>/profile")
def get_product_profile(attraction_id):
    """Public — fetch the Ministry of Tourism product profile for an attraction."""
    profile = TourismProductProfile.query.filter_by(attraction_id=attraction_id).first()
    if not profile:
        return jsonify({"error": "No product profile for this attraction"}), 404
    return jsonify(_profile_to_dict(profile)), 200


@extras_bp.put("/attractions/<uuid:attraction_id>/profile")
@jwt_required()
def upsert_product_profile(attraction_id):
    """Create or fully replace the product profile for an attraction.

    Owner/admin only. The attraction must exist.
    """
    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401

    attraction = db.session.get(Attraction, attraction_id)
    if not attraction:
        return jsonify({"error": "Attraction not found"}), 404
    if str(attraction.business_owner_id) != str(user_uuid) and not _is_admin():
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}

    profile = TourismProductProfile.query.filter_by(attraction_id=attraction_id).first()
    created = False
    if profile is None:
        profile = TourismProductProfile(attraction_id=attraction_id)
        db.session.add(profile)
        created = True
    else:
        # Replace semantics on PUT — clear writable fields first.
        for field in _PROFILE_WRITABLE_FIELDS:
            setattr(profile, field, None)

    ok, err = _apply_profile_payload(profile, data)
    if not ok:
        db.session.rollback()
        return jsonify({"error": err}), 400
    db.session.commit()

    _log_activity(user_uuid, "product_profile_upserted", "attraction", attraction_id,
                  {"created": created})
    return jsonify(_profile_to_dict(profile)), 201 if created else 200


@extras_bp.patch("/attractions/<uuid:attraction_id>/profile")
@jwt_required()
def patch_product_profile(attraction_id):
    """Partial update of the product profile."""
    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401

    profile = TourismProductProfile.query.filter_by(attraction_id=attraction_id).first()
    if not profile:
        return jsonify({"error": "No product profile for this attraction"}), 404

    attraction = db.session.get(Attraction, attraction_id)
    if attraction and str(attraction.business_owner_id) != str(user_uuid) and not _is_admin():
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json(silent=True) or {}
    ok, err = _apply_profile_payload(profile, data)
    if not ok:
        db.session.rollback()
        return jsonify({"error": err}), 400
    db.session.commit()

    _log_activity(user_uuid, "product_profile_updated", "attraction", attraction_id,
                  {"fields": list(data.keys())})
    return jsonify(_profile_to_dict(profile)), 200


@extras_bp.delete("/attractions/<uuid:attraction_id>/profile")
@jwt_required()
def delete_product_profile(attraction_id):
    user_uuid = _require_user_uuid()
    if user_uuid is None:
        return jsonify({"error": "Unauthorized"}), 401

    profile = TourismProductProfile.query.filter_by(attraction_id=attraction_id).first()
    if not profile:
        return jsonify({"error": "No product profile for this attraction"}), 404

    attraction = db.session.get(Attraction, attraction_id)
    if attraction and str(attraction.business_owner_id) != str(user_uuid) and not _is_admin():
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(profile)
    db.session.commit()
    _log_activity(user_uuid, "product_profile_deleted", "attraction", attraction_id)
    return jsonify({"message": "Product profile deleted"}), 200


@public_bp.get("/attractions/<uuid:attraction_id>/profile")
def public_product_profile(attraction_id):
    """Same shape as the /api/v1/ endpoint but on /api/public/* for tourists."""
    profile = TourismProductProfile.query.filter_by(attraction_id=attraction_id).first()
    if not profile:
        return jsonify({"error": "No product profile for this attraction"}), 404
    return jsonify(_profile_to_dict(profile)), 200


# ── Anonymous analytics ingestion (used by STORY004 search etc.) ─────────────

@extras_bp.post("/analytics/events")
def post_analytics_event():
    """Open endpoint for frontends/kiosks to record a single analytics event."""
    data = request.get_json() or {}
    event_type = data.get("event_type")
    if not event_type:
        return jsonify({"error": "event_type required"}), 400
    user_uuid = _require_user_uuid()
    _log_event(event_type, user_id=user_uuid, metadata=data.get("metadata"))
    return jsonify({"recorded": True}), 201
