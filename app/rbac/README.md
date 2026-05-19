# rbac Feature

## What This Feature Does
Role and permission management APIs with user-role and role-permission assignment.

## Install And Runtime Requirements
Install dependencies from repository root:
```bash
pipenv install
```
Relevant packages for this feature:
- flask
- flask-sqlalchemy
- flask-migrate
- marshmallow
- flask-jwt-extended
- python-dotenv

Apply migrations before testing API endpoints:
```bash
pipenv run flask --app main db upgrade
```
Start local API:
```bash
FLASK_APP=main.py pipenv run flask run --host=0.0.0.0 --port=5000
```

## Test Setup
```bash
export BASE_URL=http://127.0.0.1:5000
export JWT_ACCESS_TOKEN=<paste-valid-jwt>
export USER_ID=00000000-0000-0000-0000-000000000001
```

## Endpoint Testing

### GET /api/v1/permissions
Source: app/rbac/controllers/routes/permission_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/v1/permissions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### POST /api/v1/permissions
Source: app/rbac/controllers/routes/permission_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X POST "$BASE_URL/api/v1/permissions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"name": "perm_smoke_example", "description": "updated"}'
```

### DELETE /api/v1/permissions/<permission_id>
Source: app/rbac/controllers/routes/permission_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X DELETE "$BASE_URL/api/v1/permissions/00000000-0000-0000-0000-000000000031" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### GET /api/v1/permissions/<permission_id>
Source: app/rbac/controllers/routes/permission_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/v1/permissions/00000000-0000-0000-0000-000000000031" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### PUT /api/v1/permissions/<permission_id>
Source: app/rbac/controllers/routes/permission_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X PUT "$BASE_URL/api/v1/permissions/00000000-0000-0000-0000-000000000031" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"name": "perm_smoke_example", "description": "updated"}'
```

### POST /api/v1/role-permissions
Source: app/rbac/controllers/routes/role_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X POST "$BASE_URL/api/v1/role-permissions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"role_id": "00000000-0000-0000-0000-000000000030", "permission_id": "00000000-0000-0000-0000-000000000031"}'
```

### GET /api/v1/roles
Source: app/rbac/controllers/routes/role_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/v1/roles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### POST /api/v1/roles
Source: app/rbac/controllers/routes/role_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X POST "$BASE_URL/api/v1/roles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"name": "role_smoke_example", "description": "updated"}'
```

### DELETE /api/v1/roles/<role_id>
Source: app/rbac/controllers/routes/role_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X DELETE "$BASE_URL/api/v1/roles/00000000-0000-0000-0000-000000000030" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### GET /api/v1/roles/<role_id>
Source: app/rbac/controllers/routes/role_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/v1/roles/00000000-0000-0000-0000-000000000030" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### PUT /api/v1/roles/<role_id>
Source: app/rbac/controllers/routes/role_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X PUT "$BASE_URL/api/v1/roles/00000000-0000-0000-0000-000000000030" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"name": "role_smoke_example", "description": "updated"}'
```

### GET /api/v1/user-roles
Source: app/rbac/controllers/routes/role_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/v1/user-roles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### POST /api/v1/user-roles
Source: app/rbac/controllers/routes/role_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X POST "$BASE_URL/api/v1/user-roles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"user_id": "00000000-0000-0000-0000-000000000001", "role_id": "00000000-0000-0000-0000-000000000030", "assigned_by": "admin@example.com"}'
```

### GET /api/v1/user/<user_id>/roles
Source: app/rbac/controllers/routes/role_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/v1/user/00000000-0000-0000-0000-000000000001/roles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
