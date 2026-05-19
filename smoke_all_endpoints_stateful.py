import json
import re
import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta

from app import create_app


METHOD_ORDER = {"POST": 0, "GET": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}


def utc_now():
    return datetime.now(UTC)


def extract_id(payload):
    if isinstance(payload, dict):
        for key in ("id", "request_id", "profile_id", "reference", "intent_id"):
            val = payload.get(key)
            if isinstance(val, str) and val:
                return val
        for key in ("data", "result", "user", "registration", "profile", "payment"):
            if key in payload:
                found = extract_id(payload[key])
                if found:
                    return found
        for value in payload.values():
            found = extract_id(value)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = extract_id(item)
            if found:
                return found
    return None


def build_runner():
    app = create_app()
    client = app.test_client()

    state = {
        "user_id": "f444b66f-a0e3-4c23-a584-c8596dd18d73",
        "email": f"smoke_{uuid.uuid4().hex[:8]}@example.com",
        "password": "Pass12345!",
        "username": f"smoke_{uuid.uuid4().hex[:8]}",
        "locale": "en",
    }

    def req(method, path, payload=None, headers=None):
        h = {
            "Content-Type": "application/json",
            "X-User-Id": state.get("user_id", ""),
        }
        # Once seed_auth() has run, every authenticated endpoint should be
        # exercised with a real Bearer token rather than the X-User-Id
        # testing header. Without this the smoke run produces a flood of
        # 401s for protected routes that are actually working correctly.
        access_token = state.get("access_token")
        if access_token:
            h["Authorization"] = f"Bearer {access_token}"
        if headers:
            h.update(headers)
        resp = client.open(path=path, method=method, json=payload, headers=h)
        body = resp.get_json(silent=True)
        return resp, body

    def seed_auth():
        req("POST", "/api/v1/auth/signup", {
            "email": state["email"],
            "password": state["password"],
            "username": state["username"],
        })
        login_resp, login_body = req("POST", "/api/v1/auth/login", {
            "email": state["email"],
            "password": state["password"],
        })
        if login_resp.status_code < 400 and isinstance(login_body, dict):
            # /auth/login wraps the payload via ApiResponse.success so the
            # tokens live under "data". Fall back to top-level for
            # forward-compat with older responses.
            payload = login_body.get("data") if isinstance(login_body.get("data"), dict) else login_body
            state["access_token"] = payload.get("access_token")
            state["refresh_token"] = payload.get("refresh_token")
            user = payload.get("user") or {}
            if isinstance(user, dict) and user.get("id"):
                state["user_id"] = user["id"]

    def seed_destination():
        slug = f"smoke-destination-{uuid.uuid4().hex[:8]}"
        resp, body = req("POST", "/api/v1/destinations/", {
            "canonical_name": "Smoke Destination",
            "slug": slug,
        })
        if resp.status_code < 400:
            state["destination_id"] = extract_id(body)

        cleanup_slug = f"cleanup-destination-{uuid.uuid4().hex[:8]}"
        resp, body = req("POST", "/api/v1/destinations/", {
            "canonical_name": "Cleanup Destination",
            "slug": cleanup_slug,
        })
        if resp.status_code < 400:
            state["cleanup_destination_id"] = extract_id(body)

    def seed_amenity():
        resp, body = req("POST", "/api/v1/amenities/", {
            "name": "WiFi",
            "icon_url": "https://example.com/wifi.png",
        })
        if resp.status_code < 400:
            state["amenity_id"] = extract_id(body)

    def seed_attraction():
        if not state.get("destination_id"):
            return
        resp, body = req("POST", "/api/v1/attractions/", {
            "name": "Smoke Attraction",
            "destination_id": state["destination_id"],
            "business_owner_id": state["user_id"],
        })
        if resp.status_code < 400:
            state["attraction_id"] = extract_id(body)

    def seed_feedback_objects():
        user_email = f"feedback_{uuid.uuid4().hex[:8]}@example.com"
        resp, body = req("POST", "/api/v1/feedback/users", {
            "email": user_email,
            "password": "Pass12345!",
            "username": f"f_{uuid.uuid4().hex[:8]}",
        })
        if resp.status_code < 400:
            state["feedback_user_id"] = extract_id(body)

        resp, body = req("POST", "/api/v1/feedback/destinations", {
            "name": f"Feedback Destination {uuid.uuid4().hex[:6]}",
            "country": "Kenya",
            "city": "Nairobi",
        })
        if resp.status_code < 400:
            state["feedback_destination_id"] = extract_id(body)
        else:
            print(f"FAILED to seed feedback destination: {resp.status_code} {body}")

    def seed_rbac():
        resp, body = req("POST", "/api/v1/permissions", {
            "name": f"perm_{uuid.uuid4().hex[:8]}",
            "description": "Smoke permission",
        })
        if resp.status_code < 400:
            state["permission_linked_id"] = extract_id(body)

        resp, body = req("POST", "/api/v1/permissions", {
            "name": f"perm_{uuid.uuid4().hex[:8]}",
            "description": "Smoke permission unlinked",
        })
        if resp.status_code < 400:
            state["permission_solo_id"] = extract_id(body)

        resp, body = req("POST", "/api/v1/roles", {
            "name": f"role_{uuid.uuid4().hex[:8]}",
            "description": "Smoke role",
        })
        if resp.status_code < 400:
            state["role_linked_id"] = extract_id(body)

        resp, body = req("POST", "/api/v1/roles", {
            "name": f"role_{uuid.uuid4().hex[:8]}",
            "description": "Smoke role unlinked",
        })
        if resp.status_code < 400:
            state["role_solo_id"] = extract_id(body)

    def seed_transport():
        resp, body = req("POST", "/api/v1/transport/stations/add_station", {
            "name": "Smoke Station",
            "type": "bus_terminal",
            "city": "Nairobi",
            "country": "Kenya",
            "location": {"latitude": -1.286389, "longitude": 36.817223},
        })
        if resp.status_code < 400:
            state["station_id"] = extract_id(body)

        if state.get("station_id"):
            resp, body = req("POST", "/api/v1/transport/routes/add_route", {
                "origin_station_id": state["station_id"],
                "destination_station_id": state["station_id"],
                "type": "bus",
                "duration_minutes": 45,
                "base_fare": 120.0,
            })
            if resp.status_code < 400:
                state["route_id"] = extract_id(body)

        if state.get("route_id"):
            dep = utc_now() + timedelta(hours=1)
            arr = dep + timedelta(hours=2)
            resp, body = req("POST", "/api/v1/transport/schedules/add_schedule", {
                "transport_route_id": state["route_id"],
                "departure_time": dep.isoformat(),
                "arrival_time": arr.isoformat(),
                "available_seats": 40,
                "price": 500.0,
            })
            if resp.status_code < 400:
                state["schedule_id"] = extract_id(body)

    def seed_business_and_profile():
        def create_registration(label, user_id=None):
            payload = {
                "business_name": f"{label} {uuid.uuid4().hex[:6]}",
                "business_type": "hotel",
            }
            headers = {"X-User-Id": str(user_id)} if user_id else None
            resp, body = req("POST", "/api/v1/business/register", payload, headers=headers)
            return extract_id(body) if resp.status_code < 400 else None

        rejected_id_a = create_registration("Rejected Biz A")
        if rejected_id_a:
            req("PATCH", f"/api/v1/admin/business/registrations/{rejected_id_a}", {
                "status": "rejected",
                "rejection_reason": "Smoke rejection for patch contract",
            })
            state["rejected_request_id_a"] = rejected_id_a

        rejected_id_b = create_registration("Rejected Biz B")
        if rejected_id_b:
            req("PATCH", f"/api/v1/admin/business/registrations/{rejected_id_b}", {
                "status": "rejected",
                "rejection_reason": "Smoke rejection for patch contract",
            })
            state["rejected_request_id_b"] = rejected_id_b

        pending_id = create_registration("Pending Biz")
        if pending_id:
            state["pending_request_id"] = pending_id

        admin_pending_user_1 = state["user_id"]
        admin_pending_user_2 = state["user_id"]
        state["admin_pending_request_id"] = create_registration("Admin Pending A", user_id=admin_pending_user_1)
        state["admin_profile_pending_request_id"] = create_registration("Admin Pending B", user_id=admin_pending_user_2)

        state["business_request_id"] = (
            state.get("rejected_request_id_a")
            or state.get("rejected_request_id_b")
            or state.get("pending_request_id")
        )

        resp, body = req("GET", "/api/v1/business/profiles")
        if resp.status_code < 400 and isinstance(body, dict):
            profiles = body.get("profiles") or []
            if profiles and isinstance(profiles[0], dict):
                state["business_profile_id"] = profiles[0].get("id")

    def seed_audit():
        resp, body = req("POST", "/api/v1/audit-logs", {
            "action": "create",
            "entity_type": "destination",
            "entity_id": state.get("destination_id") or str(uuid.uuid4()),
        })
        if resp.status_code < 400:
            state["audit_log_id"] = extract_id(body)

    def seed_payments():
        resp, body = req("POST", "/api/v1/payments/stripe/create-payment-intent", {
            "amount": 1500,
            "currency": "usd",
            "metadata": {"booking_id": str(uuid.uuid4())},
        })
        if resp.status_code < 400:
            if isinstance(body, dict):
                data = body.get("data") if isinstance(body.get("data"), dict) else {}
                state["stripe_intent_id"] = (
                    data.get("paymentIntentId")
                    or body.get("payment_intent_id")
                    or body.get("intent_id")
                    or extract_id(body)
                )

        resp, body = req("POST", "/api/payments/pay/mpesa", {
            "user_id": state["user_id"],
            "amount": 10,
            "phone_number": "254700000000",
        })
        if resp.status_code < 400:
            if isinstance(body, dict):
                data = body.get("data") if isinstance(body.get("data"), dict) else {}
                state["mpesa_reference"] = data.get("reference") or extract_id(body)
                state["mpesa_checkout_id"] = data.get("checkout_request_id")

    def seed_auth_password_reset_token():
        req("POST", "/api/v1/auth/password-reset", {"email": state["email"]})
        try:
            from app.extensions import db
            from app.authandusers.models.models import PasswordReset

            token_obj = (
                db.session.query(PasswordReset)
                .order_by(PasswordReset.created_at.desc())
                .first()
            )
            if token_obj and getattr(token_obj, "token", None):
                state["password_reset_token"] = token_obj.token
        except Exception:
            pass

    def seed_all():
        print("--- Starting Seeding ---")
        seed_auth()
        print(f"Auth seeded. User ID: {state.get('user_id')}")
        seed_destination()
        print(f"Destination seeded. ID: {state.get('destination_id')}")
        seed_amenity()
        print(f"Amenity seeded. ID: {state.get('amenity_id')}")
        seed_attraction()
        print(f"Attraction seeded. ID: {state.get('attraction_id')}")
        seed_feedback_objects()
        print(f"Feedback objects seeded. User: {state.get('feedback_user_id')}, Dest: {state.get('feedback_destination_id')}")
        seed_rbac()
        print(f"RBAC seeded.")
        seed_transport()
        print(f"Transport seeded.")
        seed_business_and_profile()
        print(f"Business seeded.")
        seed_audit()
        print(f"Audit seeded.")
        seed_payments()
        print(f"Payments seeded.")
        seed_auth_password_reset_token()
        print("--- Seeding Complete ---")

    def replace_path(rule, method):
        if rule.startswith("/api/v1/amenities/<uuid:id>"):
            return rule.replace("<uuid:id>", str(state.get("amenity_id") or state.get("user_id")))
        if rule.startswith("/api/v1/attractions/<uuid:id>"):
            return rule.replace("<uuid:id>", str(state.get("attraction_id") or state.get("user_id")))
        if rule.startswith("/api/v1/destinations/<uuid:id>"):
            chosen = state.get("cleanup_destination_id") if method == "DELETE" else state.get("destination_id")
            return rule.replace("<uuid:id>", str(chosen or state.get("user_id")))
        if rule.startswith("/api/v1/feedback/users/<uuid:user_id>"):
            return rule.replace("<uuid:user_id>", str(state.get("feedback_user_id") or state.get("user_id")))
        if rule.startswith("/api/v1/feedback/destinations/<uuid:dest_id>"):
            return rule.replace("<uuid:dest_id>", str(state.get("feedback_destination_id") or state.get("destination_id") or state.get("user_id")))
        if rule.startswith("/api/v1/permissions/<permission_id>"):
            return rule.replace("<permission_id>", str(state.get("permission_solo_id") or state.get("user_id")))
        if rule.startswith("/api/v1/roles/<role_id>"):
            return rule.replace("<role_id>", str(state.get("role_solo_id") or state.get("user_id")))
        if rule.startswith("/api/v1/business/registration/<string:request_id>"):
            return rule.replace("<string:request_id>", str(state.get("rejected_request_id_a") or state.get("business_request_id") or state.get("user_id")))
        if rule.startswith("/api/v1/business/registrations/<string:request_id>"):
            return rule.replace("<string:request_id>", str(state.get("rejected_request_id_b") or state.get("business_request_id") or state.get("user_id")))
        if rule.startswith("/api/v1/business/registrations/registration/<string:request_id>"):
            return rule.replace("<string:request_id>", str(state.get("pending_request_id") or state.get("business_request_id") or state.get("user_id")))
        if rule.startswith("/api/v1/admin/business/registrations/<string:request_id>"):
            return rule.replace("<string:request_id>", str(state.get("admin_pending_request_id") or state.get("pending_request_id") or state.get("business_request_id") or state.get("user_id")))
        if rule.startswith("/api/v1/admin/business/business_profiles/registrations/<string:request_id>"):
            return rule.replace("<string:request_id>", str(state.get("admin_profile_pending_request_id") or state.get("pending_request_id") or state.get("business_request_id") or state.get("user_id")))

        mapping = {
            "id": state.get("user_id"),
            "user_id": state.get("user_id"),
            "permission_id": state.get("permission_solo_id") or state.get("user_id"),
            "role_id": state.get("role_solo_id") or state.get("user_id"),
            "request_id": state.get("business_request_id") or state.get("user_id"),
            "profile_id": state.get("business_profile_id") or state.get("user_id"),
            "route_id": state.get("route_id") or state.get("user_id"),
            "schedule_id": state.get("schedule_id") or state.get("user_id"),
            "station_id": state.get("station_id") or state.get("user_id"),
            "dest_id": state.get("feedback_destination_id") or state.get("destination_id") or state.get("user_id"),
            "intent_id": state.get("stripe_intent_id") or "pi_smoke_test",
            "reference": state.get("mpesa_reference") or "ref_smoke_test",
            "log_id": state.get("audit_log_id") or state.get("user_id"),
            "destination_id": state.get("destination_id") or state.get("user_id"),
            "attraction_id": state.get("attraction_id") or state.get("user_id"),
            "amenity_id": state.get("amenity_id") or state.get("user_id"),
            "locale": state.get("locale", "en"),
        }

        def repl(match):
            token = match.group(1)
            key = token.split(":")[-1]
            return str(mapping.get(key) or state.get("user_id"))

        return re.sub(r"<([^>]+)>", repl, rule)

    def query_for_url(url):
        if url.endswith("/transport/routes/nearby"):
            return "?latitude=-1.286389&longitude=36.817223"
        if url.endswith("/transport/stations/nearby"):
            return "?latitude=-1.286389&longitude=36.817223"
        if url.endswith("/transport/stations/search"):
            return "?city=Nairobi"
        if url.endswith("/transport/schedules/search"):
            rid = state.get("route_id")
            return f"?route_id={rid}" if rid else ""
        return ""

    def payload_for(method, route, url):
        if method not in {"POST", "PUT", "PATCH"}:
            return None

        if "/api/v1/amenities/" in route:
            return {"name": "Cafe", "icon_url": "https://example.com/cafe.png"}
        if "/api/v1/attractions/" in route:
            return {
                "name": "Updated Attraction",
                "destination_id": state.get("destination_id"),
                "business_owner_id": state.get("user_id"),
            }
        if "/api/v1/attraction-amenities/" in route:
            return {"attraction_id": state.get("attraction_id"), "amenity_id": state.get("amenity_id")}
        if "/api/v1/attraction-translations/" in route:
            return {
                "attraction_id": state.get("attraction_id"),
                "locale": state.get("locale", "en"),
                "name": "Attraction EN",
                "description": "Translated",
            }
        if "/api/v1/destinations/" in route:
            return {"canonical_name": "Updated Destination", "slug": f"updated-destination-{uuid.uuid4().hex[:6]}"}
        if "/api/v1/destination-translations/" in route:
            return {
                "destination_id": state.get("destination_id"),
                "locale": state.get("locale", "en"),
                "name": "Destination EN",
                "overview": "Translated overview",
            }
        if "/api/v1/auth/signup" in route:
            return {
                "email": f"again_{uuid.uuid4().hex[:8]}@example.com",
                "password": "Pass12345!",
                "username": f"again_{uuid.uuid4().hex[:8]}",
            }
        if "/api/v1/auth/login" in route:
            return {"email": state["email"], "password": state["password"]}
        if "/api/v1/auth/logout" in route:
            return {"refresh_token": state.get("refresh_token")}
        if "/api/v1/auth/password-reset/confirm" in route:
            return {
                "reset_token": state.get("password_reset_token") or str(uuid.uuid4()),
                "new_password": "NewPass123!",
            }
        if "/api/v1/auth/password-reset" in route:
            return {"email": state["email"]}
        if "/api/v1/business/register" in route or "/api/v1/business/registrations" in route:
            if method == "POST":
                return {
                    "business_name": f"Smoke Biz {uuid.uuid4().hex[:6]}",
                    "business_type": "hotel",
                    "registration_doc": {"certificate_url": "https://example.com/cert.pdf"},
                }
            return {"business_name": f"Updated Biz {uuid.uuid4().hex[:6]}"}
        if "/api/v1/business/registration/" in route:
            return {"business_name": f"Updated Biz {uuid.uuid4().hex[:6]}"}
        if "/api/v1/business/profile/delete" in route:
            return {"profile_id": state.get("business_profile_id") or state.get("user_id")}
        if "/api/v1/business/profile" in route:
            return {
                "business_name": "Profile Biz Update",
                "business_type": "hotel",
                "description": "Profile patch",
            }
        if "/api/v1/admin/business/" in route:
            return {"status": "approved"}
        if "/api/v1/feedback/users" in route:
            return {
                "email": f"fb_{uuid.uuid4().hex[:8]}@example.com",
                "password": "Pass12345!",
                "username": f"fb_{uuid.uuid4().hex[:8]}",
            }
        if "/api/v1/feedback/reviews" in route:
            return {
                "tourist_id": state.get("feedback_user_id") or state.get("user_id"),
                "target_type": "destination",
                "target_id": state.get("feedback_destination_id") or state.get("destination_id"),
                "rating": 4,
                "comment": "Nice",
            }
        if "/api/v1/feedback/gallery" in route:
            return {
                "target_type": "destination",
                "target_id": state.get("feedback_destination_id") or state.get("destination_id"),
                "url": "https://example.com/img2.jpg",
                "media_type": "image",
            }
        if "/api/v1/feedback/contacts" in route:
            return {
                "destination_id": state.get("feedback_destination_id") or state.get("destination_id"),
                "name": "Hospital",
                "type": "medical",
                "phone": "+254711111111",
            }
        if "/api/v1/feedback/destinations" in route:
            return {"name": f"Feedback Spot {uuid.uuid4().hex[:6]}", "country": "Kenya", "city": "Nairobi"}
        if "/api/v1/payments/stripe/create-payment-intent" in route:
            return {
                "amount": 2000,
                "currency": "usd",
                "metadata": {"booking_id": str(uuid.uuid4())},
            }
        if "/api/v1/payments/stripe/webhook" in route:
            return {
                "id": f"evt_{uuid.uuid4().hex[:18]}",
                "type": "payment_intent.succeeded",
                "data": {"object": {"id": state.get("stripe_intent_id")}},
            }
        if "/api/payments/pay/mpesa" in route:
            return {"user_id": state.get("user_id"), "amount": 10, "phone_number": "254700000000"}
        if "/api/payments/callback/mpesa" in route:
            return {
                "Body": {
                    "stkCallback": {
                        "CheckoutRequestID": state.get("mpesa_checkout_id") or "mock-checkout-id",
                        "ResultCode": 0,
                    }
                }
            }
        if "/api/v1/permissions" in route:
            return {"name": f"perm_{uuid.uuid4().hex[:8]}", "description": "updated"}
        if "/api/v1/roles" in route:
            return {"name": f"role_{uuid.uuid4().hex[:8]}", "description": "updated"}
        if "/api/v1/role-permissions" in route:
            return {
                "role_id": state.get("role_linked_id") or state.get("role_solo_id"),
                "permission_id": state.get("permission_linked_id") or state.get("permission_solo_id"),
            }
        if "/api/v1/user-roles" in route:
            return {
                "user_id": state.get("user_id"),
                "role_id": state.get("role_linked_id") or state.get("role_solo_id"),
            }
        if "/api/v1/settings/profile" in route:
            return {"full_name": "Smoke User"}
        if "/api/v1/settings/accessibility" in route:
            return {"font_size": 16}
        if "/api/v1/settings/notifications" in route:
            return {"email_alerts": True}
        if "/api/v1/settings/preferences" in route:
            return {"interests": {"culture": True, "nature": True}}
        if "/api/v1/transport/stations/add_station" in route or "/api/v1/transport/stations/" in route:
            return {
                "name": "Updated Station",
                "type": "bus_terminal",
                "city": "Nairobi",
                "country": "Kenya",
                "location": {"latitude": -1.28, "longitude": 36.82},
            }
        if "/api/v1/transport/routes/add_route" in route or "/api/v1/transport/routes/" in route:
            return {
                "origin_station_id": state.get("station_id"),
                "destination_station_id": state.get("station_id"),
                "type": "bus",
                "duration_minutes": 35,
                "base_fare": 110.0,
            }
        if "/api/v1/transport/schedules/add_schedule" in route:
            dep = utc_now() + timedelta(hours=3)
            arr = dep + timedelta(hours=1)
            return {
                "transport_route_id": state.get("route_id"),
                "departure_time": dep.isoformat(),
                "arrival_time": arr.isoformat(),
                "available_seats": 30,
                "price": 450.0,
            }
        if "/api/v1/transport/schedules/" in route and "/update_seats" in route:
            return {"available_seats": 25}
        if "/api/v1/audit-logs" in route:
            return {"action": "update", "entity_type": "destination", "entity_id": state.get("destination_id")}

        return {}

    def headers_for(url):
        h = {
            "Content-Type": "application/json",
            "X-User-Id": state.get("user_id", ""),
        }
        # /auth/refresh needs the refresh token specifically. Every other
        # authenticated endpoint takes the access token, so attach it by
        # default when we have one — otherwise the smoke run reports
        # spurious 401s for routes that are functioning correctly.
        if "/api/v1/auth/refresh" in url and state.get("refresh_token"):
            h["Authorization"] = f"Bearer {state['refresh_token']}"
        elif state.get("access_token"):
            h["Authorization"] = f"Bearer {state['access_token']}"
        if "/api/v1/payments/stripe/webhook" in url:
            h["Stripe-Signature"] = "smoke-signature"
        return h

    seed_all()

    rules = []
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/static"):
            continue
        for method in rule.methods:
            if method in METHOD_ORDER:
                rules.append((rule, method))

    rules.sort(key=lambda rm: (METHOD_ORDER[rm[1]] == 4, rm[0].rule, METHOD_ORDER[rm[1]]))

    results = []
    for rule, method in rules:
        if "/api/v1/auth/authorize/google" in rule.rule or "/api/v1/auth/login/google" in rule.rule:
            continue
        url = replace_path(rule.rule, method)
        q = query_for_url(url)
        full_url = f"{url}{q}"
        payload = payload_for(method, rule.rule, full_url)
        hdr = headers_for(full_url)
        try:
            response = client.open(path=full_url, method=method, json=payload, headers=hdr)
            body = response.get_json(silent=True)
            message = None
            if isinstance(body, dict):
                message = body.get("message") or body.get("error") or body.get("code")
                if method == "POST" and rule.rule == "/api/v1/transport/schedules/add_schedule":
                    created = extract_id(body)
                    if created:
                        state["schedule_id"] = created
                if method == "POST" and rule.rule == "/api/v1/transport/routes/add_route":
                    created = extract_id(body)
                    if created:
                        state["route_id"] = created
                if method == "POST" and rule.rule == "/api/v1/transport/stations/add_station":
                    created = extract_id(body)
                    if created:
                        state["station_id"] = created
            results.append({
                "method": method,
                "route": rule.rule,
                "url": full_url,
                "status": response.status_code,
                "message": message,
            })
        except Exception as exc:
            results.append({
                "method": method,
                "route": rule.rule,
                "url": full_url,
                "status": "EXCEPTION",
                "message": str(exc),
            })

    summary = Counter()
    for row in results:
        status = row["status"]
        if isinstance(status, int):
            summary[f"{status // 100}xx"] += 1
        else:
            summary["exception"] += 1

    failed_5xx = [r for r in results if r["status"] == "EXCEPTION" or (isinstance(r["status"], int) and r["status"] >= 500)]
    all_4xx = [r for r in results if isinstance(r["status"], int) and 400 <= r["status"] < 500]

    print("TOTAL_CALLS", len(results))
    print("SUMMARY", dict(summary))
    print("TOTAL_4XX", len(all_4xx))
    print("FAIL_5XX_OR_EXCEPTION", len(failed_5xx))

    out_path = "smoke_report_all_endpoints_stateful.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print("REPORT_FILE", out_path)


if __name__ == "__main__":
    build_runner()
