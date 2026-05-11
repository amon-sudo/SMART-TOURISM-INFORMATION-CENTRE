from app.extensions import db
from app.rbac.models.permission import Permission


def create_permission(data: dict) -> Permission:
    existing = Permission.query.filter_by(name=data["name"]).first()
    if existing:
        raise ValueError(f"Permission '{data['name']}' already exists.")

    permission = Permission(
        name=data["name"],
        description=data.get("description"),
        module=data.get("module"),
        is_active=data.get("is_active", True)
    )
    db.session.add(permission)
    db.session.commit()
    return permission


def get_all_permissions() -> list:
    return Permission.query.filter_by(is_active=True).all()


def get_permission_by_id(permission_id: int) -> Permission:
    permission = Permission.query.get(permission_id)
    if not permission:
        raise ValueError("Permission not found.")
    return permission


def update_permission(permission_id: int, data: dict) -> Permission:
    permission = Permission.query.get(permission_id)
    if not permission:
        raise ValueError("Permission not found.")

    if "name" in data and data["name"] != permission.name:
        existing = Permission.query.filter_by(name=data["name"]).first()
        if existing:
            raise ValueError(f"Permission '{data['name']}' already exists.")
        permission.name = data["name"]

    if "description" in data:
        permission.description = data["description"]

    if "module" in data:
        permission.module = data["module"]

    if "is_active" in data:
        permission.is_active = data["is_active"]

    db.session.commit()
    return permission


def delete_permission(permission_id: int) -> None:
    permission = Permission.query.get(permission_id)
    if not permission:
        raise ValueError("Permission not found.")

    db.session.delete(permission)
    db.session.commit()