# kiosk_feature Feature

## What This Feature Does
Kiosk sessions, transfer/handoff flows, and related kiosk APIs.

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
- redis
- qrcode
- pillow

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

### GET /api/admin/kiosks
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/admin/kiosks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### POST /api/admin/kiosks
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X POST "$BASE_URL/api/admin/kiosks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"example": "replace with route-specific payload"}'
```

### GET /api/admin/kiosks/<uuid:kiosk_id>
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/admin/kiosks/<uuid:kiosk_id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### PATCH /api/admin/kiosks/<uuid:kiosk_id>
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X PATCH "$BASE_URL/api/admin/kiosks/<uuid:kiosk_id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"example": "replace with route-specific payload"}'
```

### GET /api/admin/kiosks/<uuid:kiosk_id>/analytics
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X GET "$BASE_URL/api/admin/kiosks/<uuid:kiosk_id>/analytics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN"
```

### POST /api/admin/kiosks/<uuid:kiosk_id>/content-sync
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X POST "$BASE_URL/api/admin/kiosks/<uuid:kiosk_id>/content-sync" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /api/admin/kiosks/<uuid:kiosk_id>/decommission
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
```bash
curl -i -X POST "$BASE_URL/api/admin/kiosks/<uuid:kiosk_id>/decommission" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -d '{"example": "replace with route-specific payload"}'
```

### GET /api/kiosks/<uuid:kiosk_id>/content/<string:content_type>
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/kiosks/<uuid:kiosk_id>/content/<string:content_type>" \
  -H "Content-Type: application/json"
```

### POST /api/kiosks/<uuid:kiosk_id>/health-events
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/kiosks/<uuid:kiosk_id>/health-events" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /api/kiosks/<uuid:kiosk_id>/heartbeat
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/kiosks/<uuid:kiosk_id>/heartbeat" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /api/kiosks/<uuid:kiosk_id>/sessions
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/kiosks/<uuid:kiosk_id>/sessions" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /api/sessions/<uuid:session_id>/end
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/sessions/<uuid:session_id>/end" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /api/sessions/<uuid:session_id>/events
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/sessions/<uuid:session_id>/events" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### PATCH /api/sessions/<uuid:session_id>/state
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X PATCH "$BASE_URL/api/sessions/<uuid:session_id>/state" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /api/sessions/<uuid:session_id>/transfer
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/sessions/<uuid:session_id>/transfer" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### GET /api/sessions/<uuid:session_id>/transfer-status
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/sessions/<uuid:session_id>/transfer-status" \
  -H "Content-Type: application/json"
```

### GET /api/sessions/transfer/<string:token>
Source: app/kiosk_feature/kiosk/MVC_architecture/controllers/routes/kiosk_routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/sessions/transfer/public-token-example" \
  -H "Content-Type: application/json"
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
