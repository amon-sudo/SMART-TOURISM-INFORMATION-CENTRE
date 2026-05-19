import uuid
from datetime import timezone
import os

from flask import Flask

from app.extensions import db
from app.audit.models.audit_log import AuditLog
from app.user_settings.models.models import User
from app.user_settings.controllers.controllers import update_user_profile
from app.Business.Business_registration.MVC_architecture_business.Business_registration_models.Business_registration_domain.Business_registration_domain import (
    BusinessRegistrationRequest,
)
from app.Business.Business_Profile.MVC_architecture.Business_profile_models.Business_profile_domain.Business_profile_domain import (  # noqa: F401
    BusinessProfile,
)
from app.Business.Business_registration.MVC_architecture_business.Business_registration_views.Business_views.Business_registration_service import (
    action_registration_request,
)
from app.rbac.services.role_service import create_role
from app.rbac.services.permission_service import create_permission
from app.mpesa_payment_feature.services.payment_servicesmpesa import process_payment, handle_callback
from app.models.attraction_time_data import AttractionTimeData  # noqa: F401
from app.models.itinerary import Itinerary  # noqa: F401
from app.models.qr_code import QrCode  # noqa: F401
from app.models.booking import Booking, BookingStatus, BookingType, RefundStatus
from app.payment_stripe.models.models import PaymentStripe
from app.services.payment_service import PaymentService


def _make_user(email_prefix: str) -> User:
    user = User(
        email=f"{email_prefix}_{uuid.uuid4().hex[:8]}@example.com",
        username=f"{email_prefix}_{uuid.uuid4().hex[:8]}",
        password_hash="smoke-password",
    )
    db.session.add(user)
    db.session.commit()
    return user


def _count_action(action: str) -> int:
    return AuditLog.query.filter_by(action=action).count()


def _assert_action_increment(action: str, before: int, label: str) -> None:
    after = _count_action(action)
    if after <= before:
        raise AssertionError(f"Expected audit action '{action}' for {label}, before={before}, after={after}")
    print(f"PASS {label}: action={action} before={before} after={after}")


def run() -> None:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///dev.db",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

        # 1) User settings mutation -> user_profile_updated
        user = _make_user("audit_user")
        before = _count_action("user_profile_updated")
        update_user_profile(
            user_id=str(user.id),
            data={"full_name": "Audit Smoke Tester"},
            actor_user_id=str(user.id),
            ip_address="127.0.0.1",
            user_agent="smoke-audit-script",
        )
        _assert_action_increment("user_profile_updated", before, "user settings update")

        # 2) Business registration admin action -> business_registration_status_changed
        applicant = _make_user("audit_applicant")
        admin = _make_user("audit_admin")
        reg = BusinessRegistrationRequest(
            user_id=applicant.id,
            business_name=f"Smoke Biz {uuid.uuid4().hex[:6]}",
            business_type="hotel",
            status="pending",
            registration_doc={},
        )
        db.session.add(reg)
        db.session.commit()

        before = _count_action("business_registration_status_changed")
        with app.test_request_context(
            "/api/v1/admin/business/registrations/smoke",
            method="PATCH",
            headers={"User-Agent": "smoke-audit-script"},
            environ_base={"REMOTE_ADDR": "127.0.0.1"},
        ):
            action_registration_request(
                request_id=reg.id,
                admin_id=admin.id,
                action_data={"status": "approved"},
            )
        _assert_action_increment(
            "business_registration_status_changed",
            before,
            "business registration admin action",
        )

        # 3) RBAC role create -> rbac_role_created
        before = _count_action("rbac_role_created")
        create_role(
            {
                "name": f"smoke_role_{uuid.uuid4().hex[:8]}",
                "description": "Smoke role",
                "is_system": False,
            }
        )
        _assert_action_increment("rbac_role_created", before, "RBAC role creation")

        # 4) RBAC permission create -> rbac_permission_created
        before = _count_action("rbac_permission_created")
        create_permission(
            {
                "name": f"smoke_perm_{uuid.uuid4().hex[:8]}",
                "description": "Smoke permission",
                "module": "smoke",
                "action": "create",
                "scope": "global",
            }
        )
        _assert_action_increment("rbac_permission_created", before, "RBAC permission creation")

        # 5) M-Pesa flow -> mpesa_payment_status_updated
        mpesa_user = _make_user("audit_mpesa")
        process_payment(
            {
                "user_id": str(mpesa_user.id),
                "phone_number": "254700000000",
                "amount": 123,
            }
        )
        before = _count_action("mpesa_payment_status_updated")

        # Resolve latest pending payment for callback simulation.
        from app.mpesa_payment_feature.models.payment_mpesa import PaymentMpesa

        payment = (
            PaymentMpesa.query.filter_by(user_id=mpesa_user.id)
            .order_by(PaymentMpesa.created_at.desc())
            .first()
        )
        if payment is None:
            raise AssertionError("Unable to locate M-Pesa payment for callback simulation")

        handle_callback(
            {
                "Body": {
                    "stkCallback": {
                        "CheckoutRequestID": payment.checkout_request_id,
                        "ResultCode": 0,
                    }
                }
            }
        )
        _assert_action_increment(
            "mpesa_payment_status_updated",
            before,
            "M-Pesa callback status update",
        )

        # 6) Refund assessment -> payment_refund_initiated
        refund_user = _make_user("audit_refund")
        booking = Booking(
            user_id=refund_user.id,
            reference_number=f"BK-SMOKE-{uuid.uuid4().hex[:8]}",
            type=BookingType.HOTEL,
            status=BookingStatus.CONFIRMED,
            total_cost=2000.0,
            refund_status=RefundStatus.NONE,
        )
        db.session.add(booking)
        db.session.flush()

        stripe_payment = PaymentStripe(
            user_id=refund_user.id,
            amount=2000.0,
            currency="USD",
            status="succeeded",
            stripe_payment_intent_id=f"pi_smoke_{uuid.uuid4().hex[:18]}",
            payment_metadata={"booking_id": str(booking.id)},
        )
        db.session.add(stripe_payment)
        db.session.commit()

        before = _count_action("payment_refund_initiated")
        result = PaymentService.initiate_refund_assessment(booking.id)
        if not result:
            raise AssertionError("Expected refund assessment to be initiated")

        _assert_action_increment(
            "payment_refund_initiated",
            before,
            "refund assessment status transition",
        )

        latest = AuditLog.query.order_by(AuditLog.created_at.desc()).first()
        if latest:
            ts = latest.created_at.replace(tzinfo=timezone.utc).isoformat()
            print(f"LATEST action={latest.action} entity={latest.entity_type} at={ts}")

        print("\\nAll audit smoke assertions passed.")


if __name__ == "__main__":
    run()
