from flask import Blueprint, request, jsonify
from app.rbac.schemas.role_schemas import RoleCreateSchema, RoleResponseSchema
from app.rbac.services.role_service import (
    create_role,
    get_all_roles,
    get_role_by_id,
    update_role,
    delete_role,
    assign_permission_to_role,
    assign_role_to_user,
    get_user_roles
)

role_bp = Blueprint("roles", __name__, url_prefix="/api/v1")

role_create_schema = RoleCreateSchema()
role_response_schema = RoleResponseSchema()


@role_bp.post("/roles")
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


@role_bp.get("/roles")
def handle_get_roles():
    roles = get_all_roles()
    return jsonify([role_response_schema.dump(r) for r in roles]), 200


@role_bp.get("/roles/<int:role_id>")
def handle_get_role(role_id):
    try:
        role = get_role_by_id(role_id)
        return jsonify(role_response_schema.dump(role)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@role_bp.put("/roles/<int:role_id>")
def handle_update_role(role_id):
    try:
        role = update_role(role_id, request.get_json())
        return jsonify(role_response_schema.dump(role)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@role_bp.delete("/roles/<int:role_id>")
def handle_delete_role(role_id):
    try:
        delete_role(role_id)
        return jsonify({"message": "Role deleted successfully."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@role_bp.post("/role-permissions")
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


@role_bp.post("/user-roles")
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


@role_bp.get("/user/<int:user_id>/roles")
def handle_get_user_roles(user_id):
    user_roles = get_user_roles(user_id)
    return jsonify([{
        "role_id": ur.role_id,
        "role_name": ur.role.name,
        "assigned_by": ur.assigned_by,
        "assigned_at": ur.created_at.isoformat()
    } for ur in user_roles]), 200