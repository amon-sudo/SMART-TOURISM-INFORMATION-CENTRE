from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.rbac.models.user_role import UserRole
from app.rbac.models.role_permission import RolePermission
from app.rbac.models.permission import Permission


def require_permission(permission_name: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()

            user_id = get_jwt_identity()

            user_roles = UserRole.query.filter_by(user_id=user_id).all()
            if not user_roles:
                return jsonify({"error": "Access denied. No roles assigned."}), 403

            role_ids = [ur.role_id for ur in user_roles]

            role_permissions = RolePermission.query.filter(
                RolePermission.role_id.in_(role_ids)
            ).all()

            permission_ids = [rp.permission_id for rp in role_permissions]

            has_permission = Permission.query.filter(
                Permission.id.in_(permission_ids),
                Permission.name == permission_name,
                Permission.is_active == True
            ).first()

            if not has_permission:
                return jsonify({"error": f"Access denied. Required permission: '{permission_name}'."}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator