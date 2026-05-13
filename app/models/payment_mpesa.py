from app.utils.extensions import db

class PaymentMpesa(db.Model):
    __tablename__ = "payments_mpesa"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")
    reference = db.Column(db.String(100), unique=True)
    checkout_request_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
