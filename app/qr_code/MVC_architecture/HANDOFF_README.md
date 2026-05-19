# QR Code MVC — Session Handoff Addition

## Where every file lives

```
qr_code/                              ← your existing qr_code MVC folder
│
├── models/
│   ├── base.py                       existing — BaseModel mixin
│   ├── qr_code.py                    existing — persistent QR codes (itineraries, bookings)
│   └── handoff_token.py              NEW ← drop in here
│
├── services/
│   ├── qr_code_service.py            existing — persistent QR generation
│   └── handoff_service.py            NEW ← drop in here
│
├── controllers/
│   ├── qr_code_controller.py         existing — admin manage + public scan
│   └── handoff_controller.py         NEW ← drop in here
│
├── routes/
│   ├── qr_code_routes.py             existing
│   └── handoff_routes.py             NEW ← drop in here
│
├── validators/
│   ├── schemas.py                    existing — QrCodeListQuerySchema etc.
│   └── handoff_schemas.py            NEW ← drop in here
│
├── middleware/
│   └── require_admin.py              existing
│
└── migrations/
    ├── 001_create_core_tables.py     existing — qr_codes table
    └── 003_add_handoff_tokens.py     NEW ← drop in here
```

---

## One line to add in app/__init__.py

After you copy the files in, register the new blueprint:

```python
from app.routes.handoff_routes import handoff_bp
app.register_blueprint(handoff_bp, url_prefix="/api")
```

---

## Run the new migration

```bash
flask db upgrade
```

This adds:
- `handoff_tokens` table (the one-time burn tokens)
- `state` JSONB column on `kiosk_sessions` (stores the full kiosk UI snapshot)

---

## The three new API endpoints

| Method | Path | Who calls it | Auth |
|--------|------|--------------|------|
| POST | `/api/sessions/<id>/handoff` | Kiosk — tourist taps "Continue on phone" | JWT (kiosk service account) |
| GET | `/api/handoff/<token>` | Phone — scans the QR | None — token IS the credential |
| GET | `/api/sessions/<id>/handoff-status` | Kiosk — polls every 2 sec | JWT |

---

## How the full flow works

```
1. Tourist taps "Continue on phone" on kiosk screen
       │
       ▼
2. Kiosk POSTs current session state to /api/sessions/<id>/handoff
   Body: { "session_state": { step, destination, interests, itinerary_draft, ... } }
       │
       ▼
3. HandoffService:
   - Revokes any previous pending handoff QRs for this session
   - Generates a 32-char one-time token
   - Saves session state as JSONB in handoff_tokens
   - Renders QR image (fill_color="#003366")
   - Returns { handoff_url, qr_data_url, expires_in: 300 }
       │
       ▼
4. Kiosk renders the QR on screen
   Shows: "Scan this with your phone — expires in 5:00"
   Starts polling GET /api/sessions/<id>/handoff-status every 2 seconds
       │
       ▼
5. Tourist scans QR with phone
       │
       ▼
6. Phone hits GET /api/handoff/<token>
   HandoffService:
   - Looks up token → validates it's pending and not expired
   - Burns it (status = redeemed, used_at = now)
   - Issues a 15-minute mobile JWT
     (identity = kiosk_session_id, no username/password needed)
   - Returns { mobile_jwt, session_state, resume_url }
       │
       ├── Phone has tourism app installed
       │     → app intercepts tourism-app://resume?session=<id>
       │     → stores JWT, restores UI from session_state
       │
       └── Phone has only a browser
             → redirects to https://tourism.go.ke/mobile/resume/<id>
               (web fallback — same session state, browser-based UI)
       │
       ▼
7. Kiosk poll returns { transferred: true, status: "redeemed" }
   Kiosk shows: "Session sent to your phone ✓"
   Kiosk resets after 10 seconds for the next tourist
```

---

## Why this is separate from qr_code_service / QrCode model

| | QrCode (existing) | HandoffToken (new) |
|---|---|---|
| Lifetime | Weeks / permanent | 5 minutes |
| Scans | Unlimited | Exactly once (burns) |
| Purpose | Navigation redirect | Session transfer + auth |
| Auth issued | None | Mobile JWT |
| State carried | None | Full JSONB session snapshot |
| Target | itinerary / booking | kiosk_session |

They solve different problems. Keeping them separate means neither becomes complicated trying to serve both use cases.
