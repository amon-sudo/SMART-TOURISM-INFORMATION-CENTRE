from app.extensions import db
from app.audit.models.audit_log import AuditLog


def create_audit_log(data: dict) -> AuditLog:
    log = AuditLog(
        actor_user_id=data.get("actor_user_id"),
        action=data.get("action"),
        entity_type=data.get("entity_type"),
        entity_id=data.get("entity_id"),
        kiosk_id=data.get("kiosk_id"),
        old_values=data.get("old_values"),
        new_values=data.get("new_values"),
        ip_address=data.get("ip_address"),
        user_agent=data.get("user_agent"),
        extra_data=data.get("extra_data", {})
    )
    db.session.add(log)
    db.session.commit()
    return log


def get_all_audit_logs() -> list:
    return AuditLog.query.order_by(AuditLog.created_at.desc()).all()


def get_audit_log_by_id(log_id: str) -> AuditLog:
    log = AuditLog.query.get(log_id)
    if not log:
        raise ValueError("Audit log not found.")
    return log


def get_audit_logs_by_user(user_id: str) -> list:
    return AuditLog.query.filter_by(
        actor_user_id=user_id
    ).order_by(AuditLog.created_at.desc()).all()


def get_audit_logs_by_entity(entity_type: str, entity_id: str) -> list:
    return AuditLog.query.filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(AuditLog.created_at.desc()).all()


def get_audit_logs_by_action(action: str) -> list:
    return AuditLog.query.filter_by(
        action=action
    ).order_by(AuditLog.created_at.desc()).all()


def delete_audit_log(log_id: str) -> None:
    log = AuditLog.query.get(log_id)
    if not log:
        raise ValueError("Audit log not found.")
    db.session.delete(log)
    db.session.commit()