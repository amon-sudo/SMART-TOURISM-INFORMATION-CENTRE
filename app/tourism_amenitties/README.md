# tourism_amenitties Feature

## What This Feature Does
Tourism catalog APIs: destinations, attractions, amenities, and translation/association entities.

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
- geoalchemy
- shapely

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

### POST /
Source: app/tourism_amenitties/accommodation/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### GET /api/v1/amenities/
Source: app/tourism_amenitties/amenities/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/amenities/" \
  -H "Content-Type: application/json"
```

### POST /api/v1/amenities/
Source: app/tourism_amenitties/amenities/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/amenities/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Cafe", "icon_url": "https://example.com/cafe.png"}'
```

### DELETE /api/v1/amenities/<uuid:id>
Source: app/tourism_amenitties/amenities/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X DELETE "$BASE_URL/api/v1/amenities/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json"
```

### GET /api/v1/amenities/<uuid:id>
Source: app/tourism_amenitties/amenities/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/amenities/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json"
```

### PATCH /api/v1/amenities/<uuid:id>
Source: app/tourism_amenitties/amenities/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X PATCH "$BASE_URL/api/v1/amenities/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{"name": "Cafe", "icon_url": "https://example.com/cafe.png"}'
```

### GET /api/v1/attraction-amenities/
Source: app/tourism_amenitties/attraction_amenities/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/attraction-amenities/" \
  -H "Content-Type: application/json"
```

### POST /api/v1/attraction-amenities/
Source: app/tourism_amenitties/attraction_amenities/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/attraction-amenities/" \
  -H "Content-Type: application/json" \
  -d '{"attraction_id": "00000000-0000-0000-0000-000000000011", "amenity_id": "00000000-0000-0000-0000-000000000012"}'
```

### DELETE /api/v1/attraction-amenities/<uuid:attraction_id>/<uuid:amenity_id>
Source: app/tourism_amenitties/attraction_amenities/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X DELETE "$BASE_URL/api/v1/attraction-amenities/00000000-0000-0000-0000-000000000011/<uuid:amenity_id>" \
  -H "Content-Type: application/json"
```

### GET /api/v1/attraction-translations/
Source: app/tourism_amenitties/attraction_translations/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/attraction-translations/" \
  -H "Content-Type: application/json"
```

### POST /api/v1/attraction-translations/
Source: app/tourism_amenitties/attraction_translations/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/attraction-translations/" \
  -H "Content-Type: application/json" \
  -d '{"attraction_id": "00000000-0000-0000-0000-000000000011", "locale": "en", "name": "Attraction EN", "description": "Translated"}'
```

### DELETE /api/v1/attraction-translations/<uuid:attraction_id>/<string:locale>
Source: app/tourism_amenitties/attraction_translations/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X DELETE "$BASE_URL/api/v1/attraction-translations/00000000-0000-0000-0000-000000000011/en" \
  -H "Content-Type: application/json"
```

### GET /api/v1/attraction-translations/<uuid:attraction_id>/<string:locale>
Source: app/tourism_amenitties/attraction_translations/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/attraction-translations/00000000-0000-0000-0000-000000000011/en" \
  -H "Content-Type: application/json"
```

### PATCH /api/v1/attraction-translations/<uuid:attraction_id>/<string:locale>
Source: app/tourism_amenitties/attraction_translations/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X PATCH "$BASE_URL/api/v1/attraction-translations/00000000-0000-0000-0000-000000000011/en" \
  -H "Content-Type: application/json" \
  -d '{"attraction_id": "00000000-0000-0000-0000-000000000011", "locale": "en", "name": "Attraction EN", "description": "Translated"}'
```

### GET /api/v1/attractions/
Source: app/tourism_amenitties/attractions/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/attractions/" \
  -H "Content-Type: application/json"
```

### POST /api/v1/attractions/
Source: app/tourism_amenitties/attractions/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/attractions/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Attraction", "destination_id": "00000000-0000-0000-0000-000000000002", "business_owner_id": "00000000-0000-0000-0000-000000000001"}'
```

### DELETE /api/v1/attractions/<uuid:id>
Source: app/tourism_amenitties/attractions/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X DELETE "$BASE_URL/api/v1/attractions/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json"
```

### GET /api/v1/attractions/<uuid:id>
Source: app/tourism_amenitties/attractions/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/attractions/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json"
```

### PATCH /api/v1/attractions/<uuid:id>
Source: app/tourism_amenitties/attractions/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X PATCH "$BASE_URL/api/v1/attractions/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Attraction", "destination_id": "00000000-0000-0000-0000-000000000002", "business_owner_id": "00000000-0000-0000-0000-000000000001"}'
```

### GET /api/v1/destination-translations/
Source: app/tourism_amenitties/destination_translation/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/destination-translations/" \
  -H "Content-Type: application/json"
```

### POST /api/v1/destination-translations/
Source: app/tourism_amenitties/destination_translation/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/destination-translations/" \
  -H "Content-Type: application/json" \
  -d '{"destination_id": "00000000-0000-0000-0000-000000000002", "locale": "en", "name": "Destination EN", "overview": "Translated overview"}'
```

### DELETE /api/v1/destination-translations/<uuid:destination_id>/<string:locale>
Source: app/tourism_amenitties/destination_translation/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X DELETE "$BASE_URL/api/v1/destination-translations/<uuid:destination_id>/en" \
  -H "Content-Type: application/json"
```

### GET /api/v1/destination-translations/<uuid:destination_id>/<string:locale>
Source: app/tourism_amenitties/destination_translation/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/destination-translations/<uuid:destination_id>/en" \
  -H "Content-Type: application/json"
```

### PATCH /api/v1/destination-translations/<uuid:destination_id>/<string:locale>
Source: app/tourism_amenitties/destination_translation/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X PATCH "$BASE_URL/api/v1/destination-translations/<uuid:destination_id>/en" \
  -H "Content-Type: application/json" \
  -d '{"destination_id": "00000000-0000-0000-0000-000000000002", "locale": "en", "name": "Destination EN", "overview": "Translated overview"}'
```

### GET /api/v1/destinations/
Source: app/tourism_amenitties/destination/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/destinations/" \
  -H "Content-Type: application/json"
```

### POST /api/v1/destinations/
Source: app/tourism_amenitties/destination/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/destinations/" \
  -H "Content-Type: application/json" \
  -d '{"canonical_name": "Updated Destination", "slug": "updated-destination-smoke"}'
```

### DELETE /api/v1/destinations/<uuid:id>
Source: app/tourism_amenitties/destination/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X DELETE "$BASE_URL/api/v1/destinations/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json"
```

### GET /api/v1/destinations/<uuid:id>
Source: app/tourism_amenitties/destination/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/destinations/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json"
```

### PATCH /api/v1/destinations/<uuid:id>
Source: app/tourism_amenitties/destination/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X PATCH "$BASE_URL/api/v1/destinations/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{"canonical_name": "Updated Destination", "slug": "updated-destination-smoke"}'
```

### POST /events
Source: app/tourism_amenitties/events/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/events" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /room
Source: app/tourism_amenitties/accommodation/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/room" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

### POST /tours
Source: app/tourism_amenitties/events/controllers/routes.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/tours" \
  -H "Content-Type: application/json" \
  -d '{"example": "replace with route-specific payload"}'
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
