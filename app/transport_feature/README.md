# transport_feature Feature

## What This Feature Does
Transport stations, routes, schedules, seat updates, and nearby/search endpoints.

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

### DELETE /api/v1/transport/routes/<string:route_id>
Source: app/transport_feature/Transport_routes/MVC_architecture/transport_routes_controllers/transport_routes_route.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X DELETE "$BASE_URL/api/v1/transport/routes/00000000-0000-0000-0000-000000000022" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/transport/routes/<string:route_id>
Source: app/transport_feature/Transport_routes/MVC_architecture/transport_routes_controllers/transport_routes_route.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/routes/00000000-0000-0000-0000-000000000022" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### PUT /api/v1/transport/routes/<string:route_id>
Source: app/transport_feature/Transport_routes/MVC_architecture/transport_routes_controllers/transport_routes_route.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PUT "$BASE_URL/api/v1/transport/routes/00000000-0000-0000-0000-000000000022" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"example": "replace with route-specific payload"}'
```
Also supports methods: PATCH

### GET /api/v1/transport/routes/active
Source: app/transport_feature/Transport_routes/MVC_architecture/transport_routes_controllers/transport_routes_route.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/routes/active" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### POST /api/v1/transport/routes/add_route
Source: app/transport_feature/Transport_routes/MVC_architecture/transport_routes_controllers/transport_routes_route.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/transport/routes/add_route" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"origin_station_id": "00000000-0000-0000-0000-000000000024", "destination_station_id": "00000000-0000-0000-0000-000000000024", "type": "bus", "duration_minutes": 35, "base_fare": 110.0}'
```

### GET /api/v1/transport/routes/all_routes
Source: app/transport_feature/Transport_routes/MVC_architecture/transport_routes_controllers/transport_routes_route.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/routes/all_routes" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/transport/routes/nearby
Source: app/transport_feature/Transport_routes/MVC_architecture/transport_routes_controllers/transport_routes_route.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/routes/nearby" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### DELETE /api/v1/transport/schedules/<string:schedule_id>
Source: app/transport_feature/Transport_schedule/MVC_architecture/transport_schedule_controllers/transport_schedule_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X DELETE "$BASE_URL/api/v1/transport/schedules/00000000-0000-0000-0000-000000000023" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/transport/schedules/<string:schedule_id>
Source: app/transport_feature/Transport_schedule/MVC_architecture/transport_schedule_controllers/transport_schedule_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/schedules/00000000-0000-0000-0000-000000000023" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### PUT /api/v1/transport/schedules/<string:schedule_id>/update_seats
Source: app/transport_feature/Transport_schedule/MVC_architecture/transport_schedule_controllers/transport_schedule_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PUT "$BASE_URL/api/v1/transport/schedules/00000000-0000-0000-0000-000000000023/update_seats" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"available_seats": 25}'
```

### POST /api/v1/transport/schedules/add_schedule
Source: app/transport_feature/Transport_schedule/MVC_architecture/transport_schedule_controllers/transport_schedule_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/transport/schedules/add_schedule" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"transport_route_id": "00000000-0000-0000-0000-000000000022", "departure_time": "2026-05-17T10:00:00+00:00", "arrival_time": "2026-05-17T12:00:00+00:00", "available_seats": 30, "price": 450.0}'
```

### GET /api/v1/transport/schedules/all_schedules
Source: app/transport_feature/Transport_schedule/MVC_architecture/transport_schedule_controllers/transport_schedule_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/schedules/all_schedules" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/transport/schedules/search
Source: app/transport_feature/Transport_schedule/MVC_architecture/transport_schedule_controllers/transport_schedule_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/schedules/search" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### DELETE /api/v1/transport/stations/<string:station_id>
Source: app/transport_feature/Transport_stations/MVC_architecture/transport_stations_controllers/transport_stations_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X DELETE "$BASE_URL/api/v1/transport/stations/00000000-0000-0000-0000-000000000024" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/transport/stations/<string:station_id>
Source: app/transport_feature/Transport_stations/MVC_architecture/transport_stations_controllers/transport_stations_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/stations/00000000-0000-0000-0000-000000000024" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### PUT /api/v1/transport/stations/<string:station_id>
Source: app/transport_feature/Transport_stations/MVC_architecture/transport_stations_controllers/transport_stations_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X PUT "$BASE_URL/api/v1/transport/stations/00000000-0000-0000-0000-000000000024" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"example": "replace with route-specific payload"}'
```

### GET /api/v1/transport/stations/<string:station_id>/destinations
Source: app/transport_feature/Transport_stations/MVC_architecture/transport_stations_controllers/transport_stations_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/stations/00000000-0000-0000-0000-000000000024/destinations" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/transport/stations/<string:station_id>/routes
Source: app/transport_feature/Transport_stations/MVC_architecture/transport_stations_controllers/transport_stations_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/stations/00000000-0000-0000-0000-000000000024/routes" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### POST /api/v1/transport/stations/add_station
Source: app/transport_feature/Transport_stations/MVC_architecture/transport_stations_controllers/transport_stations_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X POST "$BASE_URL/api/v1/transport/stations/add_station" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"name": "Updated Station", "type": "bus_terminal", "city": "Nairobi", "country": "Kenya", "location": {"latitude": -1.28, "longitude": 36.82}}'
```

### GET /api/v1/transport/stations/all_stations
Source: app/transport_feature/Transport_stations/MVC_architecture/transport_stations_controllers/transport_stations_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/stations/all_stations" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/transport/stations/nearby
Source: app/transport_feature/Transport_stations/MVC_architecture/transport_stations_controllers/transport_stations_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/stations/nearby" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

### GET /api/v1/transport/stations/search
Source: app/transport_feature/Transport_stations/MVC_architecture/transport_stations_controllers/transport_stations_routes.py
Headers:
- Content-Type: application/json
- X-User-Id: <user-uuid>
```bash
curl -i -X GET "$BASE_URL/api/v1/transport/stations/search" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID"
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
