# authanduser Feature

## What This Feature Does
Authentication and identity endpoints: login, token refresh/logout, password reset, and Google OAuth.

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
- authlib
- requests

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

### GET /api/v1/auth/authorize/google
Source: app/authanduser/routes/google_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/auth/authorize/google" \
  -H "Content-Type: application/json"
```

### POST /api/v1/auth/login
Source: app/authanduser/routes/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "smoke_user@example.com", "password": "Pass12345!"}'
```

### GET /api/v1/auth/login/google
Source: app/authanduser/routes/google_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/auth/login/google" \
  -H "Content-Type: application/json"
```

### POST /api/v1/auth/logout
Source: app/authanduser/routes/routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X POST "$BASE_URL/api/v1/auth/logout" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"refresh_token": "paste_refresh_token_here"}'
```

### GET /api/v1/auth/me
Source: app/authanduser/routes/routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/v1/auth/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### POST /api/v1/auth/password-reset
Source: app/authanduser/routes/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/auth/password-reset" \
  -H "Content-Type: application/json" \
  -d '{"email": "smoke_user@example.com"}'
```

### POST /api/v1/auth/password-reset/confirm
Source: app/authanduser/routes/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/auth/password-reset/confirm" \
  -H "Content-Type: application/json" \
  -d '{"reset_token": "paste_reset_token_here", "new_password": "NewPass123!"}'
```

### POST /api/v1/auth/refresh
Source: app/authanduser/routes/routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X POST "$BASE_URL/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /api/v1/auth/signup
Source: app/authanduser/routes/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "smoke_user@example.com", "password": "Pass12345!", "username": "smoke_user"}'
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
