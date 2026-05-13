from app.extensions import db

class PaymentMpesa(db.Model):
    __tablename__ = "payments_mpesa"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)  # enforce FK
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # precise decimal for money
    status = db.Column(db.String(20), default="pending")
    reference = db.Column(db.String(100), unique=True)
    checkout_request_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
