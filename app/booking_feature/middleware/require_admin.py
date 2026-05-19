"""
Admin guard middleware.
Wraps a view function requiring both a valid JWT and is_admin=True in the token claims.
"""

from functools import wraps
from flask          import jsonify, abort
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def admin_required(fn):
    """
    Decorator that:
      1. Validates the JWT (same as @jwt_required())
      2. Checks for is_admin=True in the additional claims
      3. Aborts 403 if the claim is missing or False

    Usage:
        @booking_bp.route("/admin/bookings")
        @admin_required
        def admin_list():
            ...

    Or as a wrapper in url_rule registration:
        bp.add_url_rule("/admin/bookings", view_func=admin_required(admin_list))
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if not claims.get("is_admin", False):
            abort(403, description="Admin access required")
        return fn(*args, **kwargs)
    return wrapper
