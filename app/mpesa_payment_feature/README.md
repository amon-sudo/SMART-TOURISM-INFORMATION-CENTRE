# mpesa_payment_feature Feature

## What This Feature Does
M-Pesa payment initiation, callback processing, and payment status checks.

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
- requests
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

### POST /api/v1/payments/callback/mpesa
Source: app/mpesa_payment_feature/routes/payment_routesmpesa.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/payments/callback/mpesa" \
  -H "Content-Type: application/json" \
  -d '{"Body": {"stkCallback": {"CheckoutRequestID": "mock-checkout-id", "ResultCode": 0}}}'
```

### POST /api/v1/payments/pay/mpesa
Source: app/mpesa_payment_feature/routes/payment_routesmpesa.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/payments/pay/mpesa" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "00000000-0000-0000-0000-000000000001", "amount": 10, "phone_number": "254700000000"}'
```

### GET /api/v1/payments/status/<reference>
Source: app/mpesa_payment_feature/routes/payment_routesmpesa.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/payments/status/ref_smoke_test" \
  -H "Content-Type: application/json"
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
