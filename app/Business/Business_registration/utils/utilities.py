from __future__ import annotations

import math
import os
from functools import wraps
from typing import Any

from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from sqlalchemy import select

from app.Business.errors_handling import error_response


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def paginate_query(query, page: int = 1, per_page: int = 20) -> dict:
    """
    Paginate a SQLAlchemy *select* query or ORM *Query* object.

    Returns a dict with keys:
        items        – list of model instances for the current page
        page         – current page number (1-based)
        per_page     – page size
        total        – total number of matching records
        total_pages  – total number of pages
    """
    per_page = max(1, per_page)
    page = max(1, page)

    # Support both legacy Query objects and SQLAlchemy 2-style select statements
    from app.extensions import db

    if hasattr(query, "count"):
        # Legacy ORM Query
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
    else:
        # SQLAlchemy 2-style: query is a select() statement
        count_result = db.session.execute(
            select(db.func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()
        result = db.session.execute(
            query.offset((page - 1) * per_page).limit(per_page)
        )
        items = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def send_notification(user_id: Any, message: str, notification_type: str = "info") -> None:
    """
    Send an in-app notification to a user.

    Currently persists a lightweight notification record to the database.
    Extend this function to integrate email / push / WebSocket channels.

    Args:
        user_id           – UUID of the recipient user.
        message           – Human-readable notification text.
        notification_type – One of 'info', 'success', 'warning', 'error'.
    """
    try:
        from app.extensions import db
        from datetime import datetime, timezone

        # Use a generic notifications table if it exists, otherwise log only.
        notification = {
            "user_id": str(user_id),
            "message": message,
            "type": notification_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        # Placeholder: replace with real Notification model when available.
        # e.g.: db.session.add(Notification(**notification)); db.session.commit()
        import logging
        logging.getLogger(__name__).info("NOTIFICATION %s", notification)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# RBAC helpers (used by Business route files)
# ---------------------------------------------------------------------------

def user_has_role(user_id, role_name: str) -> bool:
    """Return True if the given user holds the specified role."""
    try:
        from app.models.user_role import UserRole
        from app.models.role import Role
        from app.extensions import db

        result = db.session.execute(
            select(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .where(UserRole.user_id == str(user_id), Role.name == role_name)
        ).first()
        return result is not None
    except Exception:
        return False


def _auth_disabled() -> bool:
    return os.getenv("DISABLE_AUTH", "false").strip().lower() in {"1", "true", "yes", "on"}


def _dev_user_id() -> str:
    return request.headers.get("X-User-Id", "00000000-0000-0000-0000-000000000001")


def jwt_or_dev_required():
    """Route decorator - enforce JWT unless DISABLE_AUTH=true."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if _auth_disabled():
                return fn(*args, **kwargs)
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def role_required(role_name: str):
    """Route decorator – requires the JWT user to have *role_name*."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if _auth_disabled():
                return fn(*args, **kwargs)

            verify_jwt_in_request()
            uid = get_jwt_identity() or _dev_user_id()
            if not user_has_role(uid, role_name):
                return error_response(
                    f"Role '{role_name}' required.",
                    status_code=403,
                    code="FORBIDDEN",
                    details={"required_role": role_name},
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required():
    """Route decorator – requires the JWT user to have the 'admin' role."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if _auth_disabled():
                return fn(*args, **kwargs)

            verify_jwt_in_request()
            uid = get_jwt_identity() or _dev_user_id()
            if not user_has_role(uid, "admin"):
                return error_response(
                    "Admin access required.",
                    status_code=403,
                    code="FORBIDDEN",
                    details={"required_role": "admin"},
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator
