from flask import Blueprint, request, jsonify
from app.rbac.schemas.permission_schemas import PermissionCreateSchema, PermissionResponseSchema
from app.rbac.services.permission_service import (
    create_permission,
    get_all_permissions,
    get_permission_by_id,
    update_permission,
    delete_permission
)

permission_bp = Blueprint("permissions", __name__, url_prefix="/api/v1")

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
        return jsonify(permission_response_schema.dump(permission)), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@permission_bp.get("/permissions")
def handle_get_permissions():
    permissions = get_all_permissions()
    return jsonify([permission_response_schema.dump(p) for p in permissions]), 200


@permission_bp.get("/permissions/<int:permission_id>")
def handle_get_permission(permission_id):
    try:
        permission = get_permission_by_id(permission_id)
        return jsonify(permission_response_schema.dump(permission)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@permission_bp.put("/permissions/<int:permission_id>")
def handle_update_permission(permission_id):
    try:
        permission = update_permission(permission_id, request.get_json())
        return jsonify(permission_response_schema.dump(permission)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@permission_bp.delete("/permissions/<int:permission_id>")
def handle_delete_permission(permission_id):
    try:
        delete_permission(permission_id)
        return jsonify({"message": "Permission deleted successfully."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404