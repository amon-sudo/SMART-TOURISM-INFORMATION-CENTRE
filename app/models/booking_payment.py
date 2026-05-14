import uuid
from datetime import datetime
from app.extensions import db
from app.utils.base_model import BaseUUIDModel

class Booking(BaseUUIDModel):
    __tablename__ = "bookings"

    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    kiosk_id = db.Column(db.Uuid(as_uuid=True), nullable=True)
    kiosk_session_id = db.Column(db.Uuid(as_uuid=True), nullable=True) # Future reference
    reference_number = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4())[:8].upper())
    type = db.Column(db.String(50), nullable=False) # hotel, tour, transport
    status = db.Column(db.String(50), default="pending") # pending, confirmed, cancelled, completed
    total_cost = db.Column(db.Numeric(10, 2), nullable=False)
    
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    refund_status = db.Column(db.String(50), nullable=True)

    # Relationships
    payments = db.relationship("Payment", backref="booking", lazy=True)

    def __repr__(self):
        return f"<Booking {self.reference_number} - {self.status}>"

class Payment(BaseUUIDModel):
    __tablename__ = "payments"

    booking_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("bookings.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default="pending") # pending, succeeded, failed, refunded
    transaction_id = db.Column(db.String(255), unique=True, nullable=True)
    provider = db.Column(db.String(50), nullable=False) # mpesa, stripe
    raw_response = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"<Payment {self.provider} - {self.amount} - {self.status}>"
