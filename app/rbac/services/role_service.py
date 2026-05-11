from app.extensions import db
from app.rbac.models.role import Role
from app.rbac.models.permission import Permission
from app.rbac.models.role_permission import RolePermission
from app.rbac.models.user_role import UserRole


def create_role(data: dict) -> Role:
    existing = Role.query.filter_by(name=data["name"]).first()
    if existing:
        raise ValueError(f"Role '{data['name']}' already exists.")

    role = Role(
        name=data["name"],
        description=data.get("description"),
        is_active=data.get("is_active", True)
    )
    db.session.add(role)
    db.session.commit()
    return role


def get_all_roles() -> list:
    return Role.query.filter_by(is_active=True).all()


def get_role_by_id(role_id: int) -> Role:
    role = Role.query.get(role_id)
    if not role:
        raise ValueError("Role not found.")
    return role


def update_role(role_id: int, data: dict) -> Role:
    role = Role.query.get(role_id)
    if not role:
        raise ValueError("Role not found.")

    if "name" in data and data["name"] != role.name:
        existing = Role.query.filter_by(name=data["name"]).first()
        if existing:
            raise ValueError(f"Role '{data['name']}' already exists.")
        role.name = data["name"]

    if "description" in data:
        role.description = data["description"]

    if "is_active" in data:
        role.is_active = data["is_active"]

    db.session.commit()
    return role


def delete_role(role_id: int) -> None:
    role = Role.query.get(role_id)
    if not role:
        raise ValueError("Role not found.")

    db.session.delete(role)
    db.session.commit()


def assign_permission_to_role(role_id: int, permission_id: int) -> RolePermission:
    role = Role.query.get(role_id)
    if not role:
        raise ValueError("Role not found.")

    permission = Permission.query.get(permission_id)
    if not permission:
        raise ValueError("Permission not found.")

    existing = RolePermission.query.filter_by(
        role_id=role_id,
        permission_id=permission_id
    ).first()
    if existing:
        raise ValueError("Permission already assigned to this role.")

    role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
    db.session.add(role_permission)
    db.session.commit()
    return role_permission


def assign_role_to_user(user_id: int, role_id: int, assigned_by: int) -> UserRole:
    role = Role.query.get(role_id)
    if not role:
        raise ValueError("Role not found.")

    existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
    if existing:
        raise ValueError("Role already assigned to this user.")

    user_role = UserRole(
        user_id=user_id,
        role_id=role_id,
        assigned_by=assigned_by
    )
    db.session.add(user_role)
    db.session.commit()
    return user_role


def get_user_roles(user_id: int) -> list:
    return UserRole.query.filter_by(user_id=user_id).all()