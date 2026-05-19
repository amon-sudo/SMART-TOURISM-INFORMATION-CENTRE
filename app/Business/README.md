# Business Feature

## What This Feature Does
Business registration, business profile management, and admin review/approval flows.

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

### GET /api/v1/admin/business/business_profiles/profiles
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_admin_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/business/business_profiles/profiles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/admin/business/business_profiles/profiles/<string:profile_id>
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_admin_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/business/business_profiles/profiles/00000000-0000-0000-0000-000000000021" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/admin/business/business_profiles/registrations
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_admin_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/business/business_profiles/registrations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/admin/business/business_profiles/registrations/<string:request_id>
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_admin_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/business/business_profiles/registrations/00000000-0000-0000-0000-000000000020" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### PATCH /api/v1/admin/business/business_profiles/registrations/<string:request_id>
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_admin_routes.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/admin/business/business_profiles/registrations/00000000-0000-0000-0000-000000000020" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"status": "approved"}'
```

### GET /api/v1/admin/business/registrations
Source: app/Business/Business_registration/MVC_architecture_business/Business_controllers/Business_registration_routes_admin.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/business/registrations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/admin/business/registrations/<string:request_id>
Source: app/Business/Business_registration/MVC_architecture_business/Business_controllers/Business_registration_routes_admin.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/business/registrations/00000000-0000-0000-0000-000000000020" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### PATCH /api/v1/admin/business/registrations/<string:request_id>
Source: app/Business/Business_registration/MVC_architecture_business/Business_controllers/Business_registration_routes_admin.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/admin/business/registrations/00000000-0000-0000-0000-000000000020" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID" \
  -d '{"status": "approved"}'
```

### GET /api/v1/admin/business/registrations/all_registrations
Source: app/Business/Business_registration/MVC_architecture_business/Business_controllers/Business_registration_routes_admin.py
Headers:
- Content-Type: application/json
- Authorization: Bearer <JWT_ACCESS_TOKEN>
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/admin/business/registrations/all_registrations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_ACCESS_TOKEN" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/business/profile
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/business/profile" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### PATCH /api/v1/business/profile
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/business/profile" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"business_name": "Profile Biz Update", "business_type": "hotel", "description": "Profile patch"}'
```

### PATCH /api/v1/business/profile/<string:profile_id>
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/business/profile/00000000-0000-0000-0000-000000000021" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"business_name": "Profile Biz Update", "business_type": "hotel", "description": "Profile patch"}'
```

### PATCH /api/v1/business/profile/delete
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/business/profile/delete" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"profile_id": "00000000-0000-0000-0000-000000000021"}'
```

### PATCH /api/v1/business/profile/update
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/business/profile/update" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"business_name": "Profile Biz Update", "business_type": "hotel", "description": "Profile patch"}'
```

### GET /api/v1/business/profiles
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/business/profiles" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### POST /api/v1/business/register
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/business/register" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"business_name": "Smoke Biz Ltd", "business_type": "hotel", "registration_doc": {"certificate_url": "https://example.com/cert.pdf"}}'
```

### GET /api/v1/business/registration
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/business/registration" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### PATCH /api/v1/business/registration/<string:request_id>
Source: app/Business/Business_Profile/MVC_architecture/Business_profile_Controllers/Business_profile_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/business/registration/00000000-0000-0000-0000-000000000020" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"business_name": "Updated Biz"}'
```

### GET /api/v1/business/registrations
Source: app/Business/Business_registration/MVC_architecture_business/Business_controllers/Business_registration_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/business/registrations" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### POST /api/v1/business/registrations
Source: app/Business/Business_registration/MVC_architecture_business/Business_controllers/Business_registration_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/business/registrations" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"business_name": "Updated Biz"}'
```

### PATCH /api/v1/business/registrations/<string:request_id>
Source: app/Business/Business_registration/MVC_architecture_business/Business_controllers/Business_registration_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PATCH "$BASE_URL/api/v1/business/registrations/00000000-0000-0000-0000-000000000020" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"business_name": "Updated Biz"}'
```

### POST /api/v1/business/registrations/register
Source: app/Business/Business_registration/MVC_architecture_business/Business_controllers/Business_registration_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/business/registrations/register" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"business_name": "Updated Biz"}'
```

### DELETE /api/v1/business/registrations/registration/<string:request_id>
Source: app/Business/Business_registration/MVC_architecture_business/Business_controllers/Business_registration_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X DELETE "$BASE_URL/api/v1/business/registrations/registration/00000000-0000-0000-0000-000000000020" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
