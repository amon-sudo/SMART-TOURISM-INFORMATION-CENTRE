# payment_stripe Feature

## What This Feature Does
Stripe payment intent creation, webhook handling, and payment status lookup.

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
- stripe
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

### POST /api/v1/payments/stripe/create-payment-intent
Source: app/payment_stripe/controllers/controllers.py
Headers:
- Content-Type: application/json
```bash
curl -i -X POST "$BASE_URL/api/v1/payments/stripe/create-payment-intent" \
  -H "Content-Type: application/json" \
  -d '{"amount": 2000, "currency": "usd", "metadata": {"booking_id": "00000000-0000-0000-0000-000000000050"}}'
```

### GET /api/v1/payments/stripe/payment-status/<intent_id>
Source: app/payment_stripe/controllers/controllers.py
Headers:
- Content-Type: application/json
```bash
curl -i -X GET "$BASE_URL/api/v1/payments/stripe/payment-status/pi_smoke_test" \
  -H "Content-Type: application/json"
```

### POST /api/v1/payments/stripe/webhook
Source: app/payment_stripe/controllers/controllers.py
Headers:
- Content-Type: application/json
- Stripe-Signature: <webhook-signature>
```bash
curl -i -X POST "$BASE_URL/api/v1/payments/stripe/webhook" \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: <webhook-signature>" \
  -d '{"id": "evt_test_123", "type": "payment_intent.succeeded", "data": {"object": {"id": "pi_smoke_test"}}}'
```

## Notes
- Replace placeholder UUIDs/tokens with real values from your seeded environment.
- For admin-only endpoints, use a token that has required RBAC permissions.
- For webhook endpoints, use provider-generated signatures in non-local testing.
