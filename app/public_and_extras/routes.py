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

import secrets
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    get_jwt_identity,
    verify_jwt_in_request,
    jwt_required,
)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.authanduser.services.services import AuthService
from app.authanduser.utils.utils import (
    validate_password_strength,
    verify_password,
)
from app.tourism_amenitties.attractions.models.attraction import Attraction
from app.tourism_amenitties.destination.models.destination import Destination
from app.tourism_amenitties.accommodation.models.accommodation import Accommodation
from app.tourism_amenitties.tours.models.tour_package import TourPackage
from app.feedback_media.models import EmergencyContact
from app.user_settings.models.models import (
    User,
    UserPreference,
    RefreshToken,
)
from app.utils.responses import ApiResponse
from .models import Favourite, Notification


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
    }


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
    """STORY006 — minimal GeoJSON feed of approved attractions.

    Real PostGIS geometries are not stored on Attraction yet (the location
    column is commented out — see P3 deferred notes), so each feature emits
    a null geometry. The shape matches GeoJSON so the client can render the
    points once geometries land.
    """
    attractions = (
        Attraction.query.filter(Attraction.status == "approved").all()
    )
    features = [
        {
            "type": "Feature",
            "geometry": None,  # TODO: populate when Attraction.location is restored
            "properties": {
                "id": str(a.id),
                "name": a.name,
                "category": a.category,
            },
        }
        for a in attractions
    ]
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

    def _pick(field):
        # CMS content lives in JSON columns keyed by locale on the ERD;
        # the current Destination model only has canonical_name/slug, so
        # we expose a stable shape that the client can fill once the
        # JSONB columns land.
        return getattr(destination, field, None)

    return jsonify({
        "id": str(destination.id),
        "language": lang,
        "canonical_name": destination.canonical_name,
        "slug": destination.slug,
        "overview": _pick("overview_json"),
        "culture": _pick("culture_json"),
        "weather_info": _pick("weather_info"),
        "travel_tips": _pick("travel_tips_json"),
    }), 200


@public_bp.post("/kiosk/session/reset")
def public_kiosk_reset():
    """STORY009 — give the kiosk a fresh anonymous session token.

    A real implementation persists a KioskSession; here we just mint an
    opaque token so the kiosk UI has something to bind to until the
    kiosk_feature blueprint is wired in (see deferred notes).
    """
    return jsonify({
        "session_token": secrets.token_urlsafe(32),
        "issued_at": datetime.utcnow().isoformat() + "Z",
        "idle_timeout_seconds": 180,
    }), 201


@public_bp.post("/session/qr")
def public_session_qr():
    """STORY003 — placeholder for kiosk-to-mobile QR handoff.

    The full handoff is implemented at /api/v1/sessions/<id>/handoff in
    handoff_bp; this public endpoint just returns a redirect hint so the
    visitor stories don't 404. Clients should call the v1 endpoint once
    they have a kiosk session.
    """
    return jsonify({
        "message": "Use POST /api/v1/sessions/<kiosk_session_id>/handoff once a session is established.",
        "handoff_endpoint": "/api/v1/sessions/<kiosk_session_id>/handoff",
    }), 200


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

    data = request.get_json() or {}
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
