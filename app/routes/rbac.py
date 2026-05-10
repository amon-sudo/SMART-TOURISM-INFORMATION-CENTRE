from flask import Blueprint, request, jsonify
from app.schemas.role import RoleCreateSchema, RoleResponseSchema
from app.schemas.permission import PermissionCreateSchema, PermissionResponseSchema
from app.services.role_service import (
    create_role,
    get_all_roles,
    get_role_by_id,
    update_role,
    delete_role,
    assign_permission_to_role,
    assign_role_to_user,
    get_user_roles
)
from app.services.permission_service import (
    create_permission,
    get_all_permissions,
    get_permission_by_id,
    update_permission,
    delete_permission
)

rbac_bp = Blueprint("rbac", __name__, url_prefix="/api/v1")

role_create_schema = RoleCreateSchema()
role_response_schema = RoleResponseSchema()
permission_create_schema = PermissionCreateSchema()
permission_response_schema = PermissionResponseSchema()



# ROLES


@rbac_bp.post("/roles")
def handle_create_role():
    data = request.get_json()
    errors = role_create_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 422

    try:
        role = create_role(role_create_schema.load(data))
        return jsonify(role_response_schema.dump(role)), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@rbac_bp.get("/roles")
def handle_get_roles():
    roles = get_all_roles()
    return jsonify([role_response_schema.dump(r) for r in roles]), 200


@rbac_bp.get("/roles/<int:role_id>")
def handle_get_role(role_id):
    try:
        role = get_role_by_id(role_id)
        return jsonify(role_response_schema.dump(role)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@rbac_bp.put("/roles/<int:role_id>")
def handle_update_role(role_id):
    try:
        role = update_role(role_id, request.get_json())
        return jsonify(role_response_schema.dump(role)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@rbac_bp.delete("/roles/<int:role_id>")
def handle_delete_role(role_id):
    try:
        delete_role(role_id)
        return jsonify({"message": "Role deleted successfully."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# PERMISSIONS


@rbac_bp.post("/permissions")
def handle_create_permission():
    data = request.get_json()
    errors = permission_create_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 422

    try:
        permission = create_permission(permission_create_schema.load(data))
        return jsonify(permission_response_schema.dump(permission)), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@rbac_bp.get("/permissions")
def handle_get_permissions():
    permissions = get_all_permissions()
    return jsonify([permission_response_schema.dump(p) for p in permissions]), 200


@rbac_bp.get("/permissions/<int:permission_id>")
def handle_get_permission(permission_id):
    try:
        permission = get_permission_by_id(permission_id)
        return jsonify(permission_response_schema.dump(permission)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@rbac_bp.put("/permissions/<int:permission_id>")
def handle_update_permission(permission_id):
    try:
        permission = update_permission(permission_id, request.get_json())
        return jsonify(permission_response_schema.dump(permission)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@rbac_bp.delete("/permissions/<int:permission_id>")
def handle_delete_permission(permission_id):
    try:
        delete_permission(permission_id)
        return jsonify({"message": "Permission deleted successfully."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404



# ROLE PERMISSIONS


@rbac_bp.post("/role-permissions")
def handle_assign_permission():
    data = request.get_json()
    role_id = data.get("role_id")
    permission_id = data.get("permission_id")

    if not role_id or not permission_id:
        return jsonify({"error": "role_id and permission_id are required."}), 422

    try:
        assign_permission_to_role(role_id, permission_id)
        return jsonify({"message": "Permission assigned to role successfully."}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


# USER ROLES


@rbac_bp.post("/user-roles")
def handle_assign_role_to_user():
    data = request.get_json()
    user_id = data.get("user_id")
    role_id = data.get("role_id")
    assigned_by = data.get("assigned_by")

    if not user_id or not role_id:
        return jsonify({"error": "user_id and role_id are required."}), 422

    try:
        assign_role_to_user(user_id, role_id, assigned_by)
        return jsonify({"message": "Role assigned to user successfully."}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@rbac_bp.get("/user/<int:user_id>/roles")
def handle_get_user_roles(user_id):
    user_roles = get_user_roles(user_id)
    return jsonify([{
        "role_id": ur.role_id,
        "role_name": ur.role.name,
        "assigned_by": ur.assigned_by,
        "assigned_at": ur.created_at.isoformat()
    } for ur in user_roles]), 200