# user_settings Feature

## What This Feature Does
Per-user profile, accessibility, notification, and preference settings.

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

### GET /api/v1/settings
Source: app/user_settings/views/views.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/v1/settings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### PATCH /api/v1/settings/accessibility
Source: app/user_settings/views/views.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/settings/accessibility" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"font_size": 16}'
```

### PATCH /api/v1/settings/notifications
Source: app/user_settings/views/views.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/settings/notifications" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"email_alerts": true}'
```

### PATCH /api/v1/settings/preferences
Source: app/user_settings/views/views.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/settings/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"interests": {"culture": true, "nature": true}}'
```

### PATCH /api/v1/settings/profile
Source: app/user_settings/views/views.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/settings/profile" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"full_name": "Smoke User"}'
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
