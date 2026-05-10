# SMART-TOURISM-INFORMATION-CENTRE

Flask API for RBAC (Role-Based Access Control) management.

## Requirements

- Python 3.10+
- Pipenv

## Setup And Run

1. Clone the repository.

```bash
git clone https://github.com/amon-sudo/SMART-TOURISM-INFORMATION-CENTRE.git
cd SMART-TOURISM-INFORMATION-CENTRE
```

2. Install dependencies.

```bash
pipenv install
```

3. Create `.env` and add environment variables.

```bash
touch .env
```

Add the following values to `.env`:

```env
DATABASE_URL=sqlite:///app.db
JWT_SECRET_KEY=change-this-in-production
FLASK_ENV=development
```

4. Run database migrations.

```bash
pipenv run flask --app main db upgrade
```

5. Start the server.

```bash
pipenv run python main.py
```

The API will run on:

`http://127.0.0.1:5000`

## Health Check

```bash
curl -X GET http://127.0.0.1:5000/api/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## RBAC Endpoint Checks

Use these commands in order to test role-based access endpoints.

### 1) Create a role

```bash
curl -X POST http://127.0.0.1:5000/api/v1/roles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "admin",
    "description": "Administrator role",
    "is_active": true
  }'
```

### 2) Get all roles

```bash
curl -X GET http://127.0.0.1:5000/api/v1/roles
```

### 3) Get one role by ID

```bash
curl -X GET http://127.0.0.1:5000/api/v1/roles/1
```

### 4) Update a role

```bash
curl -X PUT http://127.0.0.1:5000/api/v1/roles/1 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated administrator role",
    "is_active": true
  }'
```

### 5) Create a permission

```bash
curl -X POST http://127.0.0.1:5000/api/v1/permissions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "manage_users",
    "description": "Can manage users",
    "module": "users",
    "is_active": true
  }'
```

### 6) Get all permissions

```bash
curl -X GET http://127.0.0.1:5000/api/v1/permissions
```

### 7) Assign permission to role

```bash
curl -X POST http://127.0.0.1:5000/api/v1/role-permissions \
  -H "Content-Type: application/json" \
  -d '{
    "role_id": 1,
    "permission_id": 1
  }'
```

### 8) Assign role to user

```bash
curl -X POST http://127.0.0.1:5000/api/v1/user-roles \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 101,
    "role_id": 1,
    "assigned_by": 1
  }'
```

### 9) Get roles assigned to a user

```bash
curl -X GET http://127.0.0.1:5000/api/v1/user/101/roles
```

## Common Issues

- `no such table: roles`
  - Run: `pipenv run flask --app main db upgrade`

- `Address already in use (Port 5000)`
  - Stop any existing Flask process, then start again.
