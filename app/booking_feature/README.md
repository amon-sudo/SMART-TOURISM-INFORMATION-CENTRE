# booking_feature Feature

## What This Feature Does
Booking creation, retrieval, and booking-related QR code operations.

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

### GET /api/v1/admin/bookings
Source: app/booking_feature/controllers/routes/booking_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/bookings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/admin/qr-codes
Source: app/booking_feature/controllers/routes/qr_code_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/qr-codes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/admin/qr-codes/<uuid:qr_id>
Source: app/booking_feature/controllers/routes/qr_code_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/qr-codes/<uuid:qr_id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### POST /api/v1/admin/qr-codes/<uuid:qr_id>/regenerate
Source: app/booking_feature/controllers/routes/qr_code_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/admin/qr-codes/<uuid:qr_id>/regenerate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /api/v1/admin/qr-codes/<uuid:qr_id>/revoke
Source: app/booking_feature/controllers/routes/qr_code_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/admin/qr-codes/<uuid:qr_id>/revoke" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"example": "replace with route-specific payload"}'
```

### GET /api/v1/bookings
Source: app/booking_feature/controllers/routes/booking_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/bookings" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### POST /api/v1/bookings
Source: app/booking_feature/controllers/routes/booking_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/bookings" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"example": "replace with route-specific payload"}'
```

### GET /api/v1/bookings/<uuid:booking_id>
Source: app/booking_feature/controllers/routes/booking_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/bookings/<uuid:booking_id>" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### PATCH /api/v1/bookings/<uuid:booking_id>/cancel
Source: app/booking_feature/controllers/routes/booking_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/bookings/<uuid:booking_id>/cancel" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /api/v1/bookings/<uuid:booking_id>/qr
Source: app/booking_feature/controllers/routes/booking_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/bookings/<uuid:booking_id>/qr" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"example": "replace with route-specific payload"}'
```

### GET /api/v1/public/qr/<string:token>/scan
Source: app/booking_feature/controllers/routes/qr_code_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/public/qr/public-token-example/scan" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
