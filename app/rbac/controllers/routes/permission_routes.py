from flask import Blueprint, request, jsonify
from app.rbac.schemas.permission_schemas import PermissionCreateSchema, PermissionResponseSchema
from app.rbac.services.permission_service import (
    create_permission,
    get_all_permissions,
    get_permission_by_id,
    update_permission,
    delete_permission
)

permission_bp = Blueprint("permissions", __name__)

permission_create_schema = PermissionCreateSchema()
permission_response_schema = PermissionResponseSchema()


@permission_bp.post("/permissions")
def handle_create_permission():
    data = request.get_json()
    errors = permission_create_schema.validate(data)
    if errors:
        return jsonify({"errors": errors}), 422

    try:
        permission = create_permission(permission_create_schema.load(data))
        return jsonify({
            "message": "Permission created successfully.",
            "details": {
                "id": permission.id,
                "name": permission.name,
                "description": permission.description,
                "module": permission.module,
                "action": permission.action,
                "scope": permission.scope,
                "created_at": permission.created_at.isoformat(),
                "info": f"The '{permission.name}' permission has been created. "
                        f"It allows '{permission.action}' actions on the "
                        f"'{permission.module}' module with '{permission.scope}' scope."
            }
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@permission_bp.get("/permissions")
def handle_get_permissions():
    permissions = get_all_permissions()
    return jsonify({
        "message": f"{len(permissions)} permission(s) found in the system.",
        "permissions": [permission_response_schema.dump(p) for p in permissions]
    }), 200


@permission_bp.get("/permissions/<permission_id>")
def handle_get_permission(permission_id):
    try:
        permission = get_permission_by_id(permission_id)
        return jsonify({
            "message": f"Permission '{permission.name}' retrieved successfully.",
            "permission": permission_response_schema.dump(permission)
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@permission_bp.put("/permissions/<permission_id>")
def handle_update_permission(permission_id):
    try:
        permission = update_permission(permission_id, request.get_json())
        return jsonify({
            "message": "Permission updated successfully.",
            "details": {
                "id": permission.id,
                "name": permission.name,
                "description": permission.description,
                "module": permission.module,
                "action": permission.action,
                "scope": permission.scope,
                "updated_at": permission.updated_at.isoformat(),
                "info": f"The '{permission.name}' permission has been updated successfully."
            }
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@permission_bp.delete("/permissions/<permission_id>")
def handle_delete_permission(permission_id):
    try:
        permission = get_permission_by_id(permission_id)
        permission_name = permission.name
        delete_permission(permission_id)
        return jsonify({
            "message": "Permission deleted successfully.",
            "details": {
                "info": f"The '{permission_name}' permission has been permanently "
                        f"deleted from the system. Any roles that had this permission "
                        f"will no longer be able to perform this action."
            }
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404