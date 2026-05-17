import uuid
from datetime import datetime
from app.extensions import db
from app.utils.base_model import BaseUUIDModel

class PaymentStripe(BaseUUIDModel):
    __tablename__ = "payments_stripe"

    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    # Optional link back to the booking this payment funds. Booking.amount_paid
    # uses this to aggregate. Nullable because some payments (top-ups, etc.)
    # may not be tied to a booking.
    booking_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default="USD")
    status = db.Column(db.String(20), default="pending")  # pending, succeeded, failed, requires_payment_method
    stripe_payment_intent_id = db.Column(db.String(255), unique=True, nullable=False)
    stripe_checkout_session_id = db.Column(db.String(255), unique=True, nullable=True)
    payment_metadata = db.Column(db.JSON, default={})

    # Relationships
    # Disambiguate because multiple modules define a User class in this codebase.
    user = db.relationship("app.user_settings.models.models.User", backref=db.backref("stripe_payments", lazy=True))

    def __repr__(self):
        return f"<PaymentStripe {self.stripe_payment_intent_id} - {self.status}>"

class StripeWebhookEvent(BaseUUIDModel):
    __tablename__ = "stripe_webhook_events"

    stripe_event_id = db.Column(db.String(255), unique=True, nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<StripeWebhookEvent {self.stripe_event_id} - {self.event_type}>"
