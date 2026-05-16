from app.extensions import db
from app.utils.base_model import BaseUUIDModel

class TourPackage(BaseUUIDModel):
    __tablename__ = "tour_packages"

    operator_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("business_profiles.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    duration_days = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    max_participants = db.Column(db.Integer, default=10)
    status = db.Column(db.String, default="active")
