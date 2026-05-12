from flask import Blueprint, request, jsonify
from app.rbac.schemas.role_schemas import RoleCreateSchema, RoleResponseSchema
from app.rbac.models.role import Role
from app.rbac.models.permission import Permission
from app.rbac.models.user_role import UserRole
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
        return jsonify({
            "message": "Role created successfully.",
            "details": {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_system": role.is_system,
                "created_at": role.created_at.isoformat(),
                "info": f"The '{role.name}' role has been created and is ready to be assigned permissions."
            }
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@role_bp.get("/roles")
def handle_get_roles():
    roles = get_all_roles()
    return jsonify({
        "message": f"{len(roles)} role(s) found in the system.",
        "roles": [role_response_schema.dump(r) for r in roles]
    }), 200


@role_bp.get("/roles/<role_id>")
def handle_get_role(role_id):
    try:
        role = get_role_by_id(role_id)
        return jsonify({
            "message": f"Role '{role.name}' retrieved successfully.",
            "role": role_response_schema.dump(role)
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@role_bp.put("/roles/<role_id>")
def handle_update_role(role_id):
    try:
        role = update_role(role_id, request.get_json())
        return jsonify({
            "message": "Role updated successfully.",
            "details": {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "updated_at": role.updated_at.isoformat(),
                "info": f"The '{role.name}' role has been updated successfully."
            }
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@role_bp.delete("/roles/<role_id>")
def handle_delete_role(role_id):
    try:
        role = get_role_by_id(role_id)
        role_name = role.name
        delete_role(role_id)
        return jsonify({
            "message": "Role deleted successfully.",
            "details": {
                "info": f"The '{role_name}' role has been permanently deleted from the system."
            }
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@role_bp.post("/role-permissions")
def handle_assign_permission():
    data = request.get_json()
    role_id = data.get("role_id")
    permission_id = data.get("permission_id")

    if not role_id or not permission_id:
        return jsonify({
            "error": "Missing required fields.",
            "details": "Both role_id and permission_id are required."
        }), 422

    try:
        assign_permission_to_role(role_id, permission_id)
        role = Role.query.get(role_id)
        permission = Permission.query.get(permission_id)
        return jsonify({
            "message": "Permission successfully assigned to role.",
            "details": {
                "role": role.name,
                "permission": permission.name,
                "module": permission.module,
                "action": permission.action,
                "scope": permission.scope,
                "info": f"The '{permission.name}' permission has been granted to the '{role.name}' role. "
                        f"Users with the '{role.name}' role can now perform '{permission.action}' "
                        f"actions on the '{permission.module}' module."
            }
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@role_bp.post("/user-roles")
def handle_assign_role_to_user():
    data = request.get_json()
    user_id = data.get("user_id")
    role_id = data.get("role_id")
    assigned_by = data.get("assigned_by")

    if not user_id or not role_id:
        return jsonify({
            "error": "Missing required fields.",
            "details": "Both user_id and role_id are required."
        }), 422

    try:
        assign_role_to_user(user_id, role_id, assigned_by)
        role = Role.query.get(role_id)
        return jsonify({
            "message": "Role successfully assigned to user.",
            "details": {
                "user_id": user_id,
                "role": role.name,
                "assigned_by": assigned_by,
                "info": f"User '{user_id}' has been granted the '{role.name}' role "
                        f"by '{assigned_by}'. This user can now perform all actions "
                        f"permitted under the '{role.name}' role."
            }
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@role_bp.get("/user-roles")
def handle_get_all_user_roles():
    user_roles = UserRole.query.all()
    result = []
    for ur in user_roles:
        role = Role.query.get(ur.role_id)
        result.append({
            "user_id": ur.user_id,
            "role": {
                "id": role.id,
                "name": role.name,
                "description": role.description
            },
            "assigned_by": ur.assigned_by,
            "assigned_at": ur.assigned_at.isoformat()
        })
    return jsonify({
        "message": f"{len(result)} user role assignment(s) found.",
        "assignments": result
    }), 200


@role_bp.get("/user/<user_id>/roles")
def handle_get_user_roles(user_id):
    user_roles = get_user_roles(user_id)
    if not user_roles:
        return jsonify({
            "message": f"No roles found for user '{user_id}'.",
            "roles": []
        }), 200

    result = []
    for ur in user_roles:
        role = Role.query.get(ur.role_id)
        result.append({
            "role_id": role.id,
            "role_name": role.name,
            "role_description": role.description,
            "assigned_by": ur.assigned_by,
            "assigned_at": ur.assigned_at.isoformat()
        })

    return jsonify({
        "message": f"User '{user_id}' has {len(result)} role(s) assigned.",
        "user_id": user_id,
        "roles": result
    }), 200