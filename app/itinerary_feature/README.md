# itinerary_feature Feature

## What This Feature Does
Itinerary CRUD and itinerary generation/analytics ingestion endpoints.

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
- flask-limiter

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

### POST /api/v1/admin/attractions/<uuid:attraction_id>/time-data
Source: app/itinerary_feature/MVC_architecture/controllers/routes/generator_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/admin/attractions/00000000-0000-0000-0000-000000000011/time-data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"avg_minutes": 90, "sample_size": 25, "source": "operator_observation"}'
```

### POST /api/v1/internal/analytics/visit-duration
Source: app/itinerary_feature/MVC_architecture/controllers/routes/generator_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/internal/analytics/visit-duration" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"attraction_id": "00000000-0000-0000-0000-000000000011", "avg_minutes": 85, "sample_size": 110}'
```

### GET /api/v1/itineraries
Source: app/itinerary_feature/MVC_architecture/controllers/routes/itinerary_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/itineraries" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### POST /api/v1/itineraries
Source: app/itinerary_feature/MVC_architecture/controllers/routes/itinerary_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/itineraries" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"title": "Weekend in Nairobi", "destination_id": "00000000-0000-0000-0000-000000000002", "start_date": "2026-06-01", "end_date": "2026-06-03"}'
```

### DELETE /api/v1/itineraries/<uuid:itinerary_id>
Source: app/itinerary_feature/MVC_architecture/controllers/routes/itinerary_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X DELETE "$BASE_URL/api/v1/itineraries/00000000-0000-0000-0000-000000000010" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/itineraries/<uuid:itinerary_id>
Source: app/itinerary_feature/MVC_architecture/controllers/routes/itinerary_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/itineraries/00000000-0000-0000-0000-000000000010" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### PATCH /api/v1/itineraries/<uuid:itinerary_id>
Source: app/itinerary_feature/MVC_architecture/controllers/routes/itinerary_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/itineraries/00000000-0000-0000-0000-000000000010" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"title": "Weekend in Nairobi", "destination_id": "00000000-0000-0000-0000-000000000002", "start_date": "2026-06-01", "end_date": "2026-06-03"}'
```

### POST /api/v1/itineraries/<uuid:itinerary_id>/publish
Source: app/itinerary_feature/MVC_architecture/controllers/routes/itinerary_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/itineraries/00000000-0000-0000-0000-000000000010/publish" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"title": "Weekend in Nairobi", "destination_id": "00000000-0000-0000-0000-000000000002", "start_date": "2026-06-01", "end_date": "2026-06-03"}'
```

### POST /api/v1/itineraries/<uuid:itinerary_id>/qr
Source: app/itinerary_feature/MVC_architecture/controllers/routes/itinerary_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/itineraries/00000000-0000-0000-0000-000000000010/qr" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"title": "Weekend in Nairobi", "destination_id": "00000000-0000-0000-0000-000000000002", "start_date": "2026-06-01", "end_date": "2026-06-03"}'
```

### POST /api/v1/itineraries/generate
Source: app/itinerary_feature/MVC_architecture/controllers/routes/generator_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/itineraries/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"destination_id": "00000000-0000-0000-0000-000000000002", "trip_days": 3, "interests": ["culture", "nature"], "budget": "medium"}'
```

### GET /api/v1/public/itineraries/<string:token>
Source: app/itinerary_feature/MVC_architecture/controllers/routes/itinerary_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/public/itineraries/public-token-example" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
