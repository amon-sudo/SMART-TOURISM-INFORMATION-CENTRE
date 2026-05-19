# audit Feature

## What This Feature Does
Audit log APIs and services for recording important state-changing actions.

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

### GET /api/v1/audit-logs
Source: app/audit/controllers/routes/audit_log_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/audit-logs" \
  -H "Content-Type: application/json"
```

### POST /api/v1/audit-logs
Source: app/audit/controllers/routes/audit_log_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/audit-logs" \
  -H "Content-Type: application/json" \
  -d '{"action": "update", "entity_type": "destination", "entity_id": "00000000-0000-0000-0000-000000000002"}'
```

### DELETE /api/v1/audit-logs/<log_id>
Source: app/audit/controllers/routes/audit_log_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X DELETE "$BASE_URL/api/v1/audit-logs/00000000-0000-0000-0000-000000000040" \
  -H "Content-Type: application/json"
```

### GET /api/v1/audit-logs/<log_id>
Source: app/audit/controllers/routes/audit_log_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/audit-logs/00000000-0000-0000-0000-000000000040" \
  -H "Content-Type: application/json"
```

### GET /api/v1/audit-logs/action/<action>
Source: app/audit/controllers/routes/audit_log_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/audit-logs/action/<action>" \
  -H "Content-Type: application/json"
```

### GET /api/v1/audit-logs/entity/<entity_type>/<entity_id>
Source: app/audit/controllers/routes/audit_log_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/audit-logs/entity/<entity_type>/<entity_id>" \
  -H "Content-Type: application/json"
```

### GET /api/v1/audit-logs/user/<user_id>
Source: app/audit/controllers/routes/audit_log_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/audit-logs/user/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json"
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
