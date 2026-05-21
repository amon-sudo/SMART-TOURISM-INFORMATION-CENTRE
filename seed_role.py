from app import create_app
from app.extensions import db
from app.rbac.models.role import Role
from app.rbac.models.permission import Permission
from app.rbac.models.role_permission import RolePermission

SYSTEM_ROLES = [
    {"name": "admin", "description": "Full system access", "is_system": True},
    {"name": "vendor", "description": "Business owner / attraction operator", "is_system": True},
    {"name": "tourist", "description": "End user / visitor", "is_system": True},
]

PERMISSIONS = [
    {"name": "business.create", "module": "business", "action": "create", "scope": "own"},
    {"name": "business.approve", "module": "business", "action": "approve", "scope": "all"},
    {"name": "business.reject", "module": "business", "action": "reject", "scope": "all"},
    {"name": "business.view_all", "module": "business", "action": "read", "scope": "all"},
    {"name": "kiosks.create", "module": "kiosks", "action": "create", "scope": "own"},
    {"name": "kiosks.manage_all", "module": "kiosks", "action": "manage", "scope": "all"},
    {"name": "kiosks.decommission", "module": "kiosks", "action": "decommission", "scope": "all"},
    {"name": "users.view_all", "module": "users", "action": "read", "scope": "all"},
    {"name": "users.deactivate", "module": "users", "action": "deactivate", "scope": "all"},
    {"name": "audit.view", "module": "audit", "action": "read", "scope": "all"},
]

ROLE_PERMISSIONS = {
    "admin": [p["name"] for p in PERMISSIONS],
    "vendor": ["business.create", "kiosks.create"],
    "tourist": [],
}

app = create_app()

with app.app_context():
    perm_map = {}
    for p_data in PERMISSIONS:
        perm = Permission.query.filter_by(name=p_data["name"]).first()
        if not perm:
            perm = Permission(**p_data)
            db.session.add(perm)
            db.session.flush()
        perm_map[p_data["name"]] = perm

    for r_data in SYSTEM_ROLES:
        role = Role.query.filter_by(name=r_data["name"]).first()
        if not role:
            role = Role(**r_data)
            db.session.add(role)
            db.session.flush()

        existing_perms = {rp.permission_id for rp in role.permissions}
        for perm_name in ROLE_PERMISSIONS.get(role.name, []):
            perm = perm_map.get(perm_name)
            if perm and perm.id not in existing_perms:
                db.session.add(RolePermission(role_id=role.id, permission_id=perm.id))

    db.session.commit()
    print("Done — roles and permissions seeded.")