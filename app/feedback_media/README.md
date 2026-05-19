# feedback_media Feature

## What This Feature Does
Tourist feedback modules: users, reviews, media gallery, emergency contacts, and destination feedback records.

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

### GET /api/v1/feedback/contacts
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/feedback/contacts" \
  -H "Content-Type: application/json"
```

### POST /api/v1/feedback/contacts
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/feedback/contacts" \
  -H "Content-Type: application/json" \
  -d '{"destination_id": "00000000-0000-0000-0000-000000000002", "name": "Hospital", "type": "medical", "phone": "+254711111111"}'
```

### GET /api/v1/feedback/destinations
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/feedback/destinations" \
  -H "Content-Type: application/json"
```

### POST /api/v1/feedback/destinations
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/feedback/destinations" \
  -H "Content-Type: application/json" \
  -d '{"name": "Feedback Spot", "country": "Kenya", "city": "Nairobi"}'
```

### DELETE /api/v1/feedback/destinations/<uuid:dest_id>
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X DELETE "$BASE_URL/api/v1/feedback/destinations/00000000-0000-0000-0000-000000000002" \
  -H "Content-Type: application/json"
```

### GET /api/v1/feedback/destinations/<uuid:dest_id>
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/feedback/destinations/00000000-0000-0000-0000-000000000002" \
  -H "Content-Type: application/json"
```

### PUT /api/v1/feedback/destinations/<uuid:dest_id>
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X PUT "$BASE_URL/api/v1/feedback/destinations/00000000-0000-0000-0000-000000000002" \
  -H "Content-Type: application/json" \
  -d '{"name": "Feedback Spot", "country": "Kenya", "city": "Nairobi"}'
```

### GET /api/v1/feedback/gallery
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/feedback/gallery" \
  -H "Content-Type: application/json"
```

### POST /api/v1/feedback/gallery
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/feedback/gallery" \
  -H "Content-Type: application/json" \
  -d '{"target_type": "destination", "target_id": "00000000-0000-0000-0000-000000000002", "url": "https://example.com/img2.jpg", "media_type": "image"}'
```

### GET /api/v1/feedback/reviews
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/feedback/reviews" \
  -H "Content-Type: application/json"
```

### POST /api/v1/feedback/reviews
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/feedback/reviews" \
  -H "Content-Type: application/json" \
  -d '{"tourist_id": "00000000-0000-0000-0000-000000000001", "target_type": "destination", "target_id": "00000000-0000-0000-0000-000000000002", "rating": 4, "comment": "Nice"}'
```

### GET /api/v1/feedback/users
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/feedback/users" \
  -H "Content-Type: application/json"
```

### POST /api/v1/feedback/users
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/feedback/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "fb_user@example.com", "password": "Pass12345!", "username": "fb_user"}'
```

### DELETE /api/v1/feedback/users/<uuid:user_id>
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X DELETE "$BASE_URL/api/v1/feedback/users/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json"
```

### GET /api/v1/feedback/users/<uuid:user_id>
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/feedback/users/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json"
```

### PUT /api/v1/feedback/users/<uuid:user_id>
Source: app/feedback_media/views.py
Headers:
- Content-Type: application/json
```bash
curl -i -X PUT "$BASE_URL/api/v1/feedback/users/00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{"email": "fb_user@example.com", "password": "Pass12345!", "username": "fb_user"}'
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
