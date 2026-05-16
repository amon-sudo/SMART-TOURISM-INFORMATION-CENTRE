from flask import Blueprint, request, jsonify
from app.audit.schemas.audit_log_schema import AuditLogCreateSchema, AuditLogResponseSchema
from app.audit.services.audit_log_service import (
    create_audit_log,
    get_all_audit_logs,
    get_audit_log_by_id,
    get_audit_logs_by_user,
    get_audit_logs_by_entity,
    get_audit_logs_by_action,
    delete_audit_log
)

audit_bp = Blueprint("audit", __name__)

audit_log_create_schema = AuditLogCreateSchema()
audit_log_response_schema = AuditLogResponseSchema()


@audit_bp.post("/audit-logs")
def handle_create_audit_log():
    data = request.get_json()
    errors = audit_log_create_schema.validate(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 422

    try:
        log = create_audit_log(audit_log_create_schema.load(data))
        return jsonify({
            "success": True,
            "message": "Audit log created successfully.",
            "details": {
                "id": log.id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "actor_user_id": log.actor_user_id,
                "created_at": log.created_at.isoformat(),
                "info": f"Action '{log.action}' on '{log.entity_type}' has been logged successfully."
            }
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@audit_bp.get("/audit-logs")
def handle_get_all_audit_logs():
    logs = get_all_audit_logs()
    return jsonify({
        "success": True,
        "message": f"{len(logs)} audit log(s) found.",
        "audit_logs": [audit_log_response_schema.dump(log) for log in logs]
    }), 200


@audit_bp.get("/audit-logs/user/<user_id>")
def handle_get_audit_logs_by_user(user_id):
    logs = get_audit_logs_by_user(user_id)
    return jsonify({
        "success": True,
        "message": f"{len(logs)} audit log(s) found for user '{user_id}'.",
        "user_id": user_id,
        "audit_logs": [audit_log_response_schema.dump(log) for log in logs]
    }), 200


@audit_bp.get("/audit-logs/entity/<entity_type>/<entity_id>")
def handle_get_audit_logs_by_entity(entity_type, entity_id):
    logs = get_audit_logs_by_entity(entity_type, entity_id)
    return jsonify({
        "success": True,
        "message": f"{len(logs)} audit log(s) found for {entity_type} '{entity_id}'.",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "audit_logs": [audit_log_response_schema.dump(log) for log in logs]
    }), 200


@audit_bp.get("/audit-logs/action/<action>")
def handle_get_audit_logs_by_action(action):
    logs = get_audit_logs_by_action(action)
    return jsonify({
        "success": True,
        "message": f"{len(logs)} audit log(s) found for action '{action}'.",
        "action": action,
        "audit_logs": [audit_log_response_schema.dump(log) for log in logs]
    }), 200


@audit_bp.get("/audit-logs/<log_id>")
def handle_get_audit_log(log_id):
    try:
        log = get_audit_log_by_id(log_id)
        return jsonify({
            "success": True,
            "message": "Audit log retrieved successfully.",
            "audit_log": audit_log_response_schema.dump(log)
        }), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404


@audit_bp.delete("/audit-logs/<log_id>")
def handle_delete_audit_log(log_id):
    try:
        log = get_audit_log_by_id(log_id)
        log_action = log.action
        log_entity = log.entity_type
        delete_audit_log(log_id)
        return jsonify({
            "success": True,
            "message": "Audit log deleted successfully.",
            "details": {
                "info": f"Audit log for action '{log_action}' on '{log_entity}' "
                        f"has been permanently deleted from the system."
            }
        }), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404