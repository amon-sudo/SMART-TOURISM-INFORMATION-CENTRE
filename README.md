
# Smart Tourism Information Centre — Backend API

Flask + PostgreSQL backend for the Digital Smart Tourism Information Centre. Powers the visitor kiosks, mobile/web apps, business owner portal, and admin dashboard.

- **214 routes** across auth, public catalog, recommendations, itineraries, bookings, payments (Stripe + M-Pesa), notifications, business onboarding, kiosk operations, transport, and admin analytics.
- JWT auth, rate limiting, security headers, alembic-managed schema.

---


## Setup notes

1. Copy `.env-example` to `.env` and fill in all required secrets and config values:
   ```bash
   cp .env-example .env
   # Then edit .env and set your secrets
   ```

2. For production, use a strong, unique password for your database user (do not use the default in the example).

3. If you are using Flask 2.x+, you may need to run migrations with:
   ```bash
   pipenv run flask --app main db upgrade
   ```

4. If you are on Windows or using WSL, ensure PostgreSQL and Python 3.11+ are installed and available in your PATH.

5. If you use Redis for rate limiting, ensure it is running and the URI is set in `.env`.

6. System dependencies (required for some Python packages):
   - Ubuntu/Debian: `sudo apt-get install build-essential libpq-dev`
   - macOS: `brew install postgresql`

---

```bash
# 1. Install dependencies
pipenv install

# 2. Activate the virtualenv
pipenv shell

# 3. Make sure Postgres is running and create the database
psql -U postgres -c "CREATE DATABASE smart_tourism_db;"
psql -U postgres -c "CREATE USER group_user WITH PASSWORD 'teamwork123';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE smart_tourism_db TO group_user;"

# 4. Apply database migrations
flask db upgrade

# 5. (Optional) wipe + reseed dev data
python recreate_db.py

# 6. Run
python main.py
```

Server starts on **http://localhost:5000**.

Health check:
```bash
curl http://localhost:5000/api/v1/health
```

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ (tested on 3.14) |
| Pipenv | latest |
| PostgreSQL | 14+ |
| Redis | optional (production rate-limit storage) |

---

## Environment variables

All config lives in `.env` at the project root. The minimum needed to boot:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `SECRET_KEY` | Flask session/CSRF signing |
| `JWT_SECRET_KEY` | JWT signing key (different from SECRET_KEY) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth ([Cloud Console](https://console.cloud.google.com/apis/credentials)) |
| `STRIPE_SECRET_KEY` | Stripe secret API key (`sk_test_...` or `sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret — see **Stripe webhook setup** below |
| `FRONTEND_OAUTH_REDIRECT_URL` | Where Google OAuth bounces the user after sign-in (e.g. `http://localhost:3000/profile`) |

Optional but recommended for production:

| Variable | Default | Notes |
|---|---|---|
| `CORS_ORIGINS` | `*` | Comma-separated allowlist of frontend origins |
| `ENABLE_SECURITY_HEADERS` | `false` | Set `true` in prod to enable Talisman (CSP, HSTS, X-Frame-Options) |
| `RATELIMIT_STORAGE_URI` | in-memory | Set to `redis://...` so rate-limit counters are shared across workers |
| `USE_POSTGIS` | `false` | Set `true` if PostGIS extension is installed (enables geography columns) |
| `MPESA_CONSUMER_KEY` / `MPESA_CONSUMER_SECRET` / `MPESA_SHORTCODE` / `MPESA_PASSKEY` / `MPESA_CALLBACK_URL` | — | Daraja API credentials |

---

## Database setup

The schema is managed by Alembic. Migration files live in `migrations/versions/`.

```bash
flask db upgrade            # apply all pending migrations
flask db current            # show current head
flask db history            # full migration chain
```

Reset the dev database from scratch (drops everything!):
```bash
python recreate_db.py
```

**Important:** Never delete or modify old migration scripts. Only add new ones for schema changes. This ensures all contributors can upgrade their databases reliably.

---

## Running the server

```bash
pipenv run python main.py
```

Or, inside the virtualenv:
```bash
python main.py
```

Server is at **http://localhost:5000**. Hot-reload is on when `FLASK_DEBUG=True`.

### Stopping cleanly

`Ctrl+C` in the terminal. If port 5000 stays bound after a crash (Windows):
```powershell
Get-NetTCPConnection -LocalPort 5000 | Select OwningProcess
taskkill /F /PID <pid>
```

---

## Stripe webhook setup

The `/api/v1/payments/stripe/webhook` endpoint validates incoming events using `STRIPE_WEBHOOK_SECRET`. Without it, webhook calls are rejected.

### Local development (using Stripe CLI)

1. **Install the Stripe CLI:** https://stripe.com/docs/stripe-cli
2. **Log in once:**
   ```bash
   stripe login
   ```
3. **Forward Stripe events to your local server:**
   ```bash
   stripe listen --forward-to localhost:5000/api/v1/payments/stripe/webhook
   ```
4. The CLI will print something like:
   ```
   > Ready! Your webhook signing secret is whsec_abcd1234efgh5678...
   ```
5. **Copy that `whsec_...` value into `.env`:**
   ```
   STRIPE_WEBHOOK_SECRET=whsec_abcd1234efgh5678...
   ```
6. Restart Flask so it picks up the new env var.
7. Trigger a test event in another terminal:
   ```bash
   stripe trigger payment_intent.succeeded
   ```
   You should see the event arrive in your Flask logs.

### Production

1. Go to the [Stripe Dashboard → Developers → Webhooks](https://dashboard.stripe.com/webhooks).
2. **Add endpoint** → URL: `https://your-domain.com/api/v1/payments/stripe/webhook`
3. Select events to subscribe to (at minimum: `payment_intent.succeeded`, `payment_intent.payment_failed`, `checkout.session.completed`).
4. After creating it, click the endpoint → **Signing secret** → **Click to reveal** → copy the `whsec_...` value.
5. Set `STRIPE_WEBHOOK_SECRET=whsec_...` in your production environment.

---

## Google OAuth setup

In [Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs](https://console.cloud.google.com/apis/credentials), add to **Authorized redirect URIs**:

```
http://localhost:5000/api/v1/auth/authorize/google     # local
https://api.your-domain.com/api/v1/auth/authorize/google   # production
```

And to **Authorized JavaScript origins**:
```
http://localhost:5000
http://localhost:3000
https://api.your-domain.com
```

---

## API documentation

A Postman collection with **111 ready-to-run requests** across 20 folders is at the project root:

```
Smart_Tourism_API.postman_collection.json
```

Import it in Postman → File → Import. The Login request auto-captures JWT tokens into collection variables so every subsequent request just works.

For a quick reference, hit:
```
GET http://localhost:5000/api/v1/health
GET http://localhost:5000/api/public/welcome
GET http://localhost:5000/api/v1/auth/oauth/debug
```

---

## Testing

### Smoke test
Smoke-test every registered endpoint end-to-end:
```bash
python smoke_all_endpoints_stateful.py
```
Reads results into `smoke_report_all_endpoints_stateful.json`. Expected: zero 5xx, zero exceptions. Any 4xx are auth/validation paths the smoke deliberately exercises.

### Unit tests
If you add or maintain code, run the unit tests:
```bash
pytest
# or
python -m unittest discover
```
If you do not have pytest/unittest installed, add it to your Pipfile and run `pipenv install`.

---

## Project layout

```
app/
  __init__.py                  app factory + blueprint registration
  extensions.py                shared db / jwt / cache / limiter instances
  authanduser/                 auth flow, JWT, password reset
  user_settings/               profile, preferences, accessibility, notifications
  tourism_amenitties/          destinations, attractions, accommodations, events, tours, amenities
  booking_feature/             bookings + items + statuses
  itinerary_feature/           AI itinerary generation + management
  feedback_media/              reviews, media gallery, emergency contacts
  payment_stripe/              Stripe payments
  mpesa_payment_feature/       M-Pesa Daraja STK push
  kiosk_feature/               kiosk device + session + transfer + analytics
  transport_feature/           stations, routes, schedules
  qr_code/                     QR generation + kiosk → phone handoff
  Business/                    business owner registration + profiles
  RBAC/                        roles + permissions + user-role assignments
  audit_log/                   admin audit trail
  public_and_extras/           public routes + analytics tables + new features
  services/                    cross-feature service singletons
  utils/                       shared helpers (responses, base model, oauth)
migrations/versions/           Alembic migration files
main.py                        entry point — runs the dev server
recreate_db.py                 wipes + reseeds dev database
smoke_all_endpoints_stateful.py  end-to-end smoke runner
Smart_Tourism_API.postman_collection.json  Postman v2.1 collection
```

---

## Security

| Feature | Where |
|---|---|
| Rate limiting | Flask-Limiter — 120/min global, 5/min on `/auth/login`, 3/min on `/auth/password-reset` |
| Security headers | Flask-Talisman (CSP/HSTS/X-Frame-Options), enabled when `ENABLE_SECURITY_HEADERS=true` |
| CORS | restricted via `CORS_ORIGINS` env var |
| Password policy | ≥8 chars, 1 uppercase, 1 digit, 1 special character |
| JWT | 1-hour access token, 7-day refresh token with revoke-on-logout / revoke-all support |
| Audit logging | every admin write recorded to `admin_audit_log` |

---

## Common commands

```bash
pipenv install              # install deps
pipenv shell                # activate venv
python main.py              # run dev server
flask db upgrade            # apply migrations
flask db migrate -m "msg"   # autogenerate a new migration
python recreate_db.py       # wipe + reseed dev DB
python smoke_all_endpoints_stateful.py  # smoke test
```

---

## Troubleshooting

**"Missing 'jwks_uri' in metadata"** when signing in with Google
→ `STRIPE_WEBHOOK_SECRET` or the OAuth `server_metadata_url` is wrong. Make sure you restarted the Flask process after editing `.env`.

**"redirect_uri_mismatch" from Google**
→ Add `http://localhost:5000/api/v1/auth/authorize/google` to the OAuth client's **Authorized redirect URIs** in Google Cloud Console.

**`type "geography" does not exist`**
→ PostGIS extension isn't installed. Either install it (`CREATE EXTENSION postgis;`) or leave `USE_POSTGIS=false`.

**`flask db upgrade` says "Can't locate revision identified by ..."**
→ Your `alembic_version` table is out of sync. Run `flask db stamp head` to mark the DB at the latest migration, then re-run upgrade.

**Login returns 429**
→ Rate limit. 5 failed login attempts per minute per IP. Wait or use a different IP.

**Port 5000 already in use (Windows)**
```powershell
Get-NetTCPConnection -LocalPort 5000 | Select OwningProcess
taskkill /F /PID <pid>
```

---

## License

Proprietary — Moringa School capstone project.
