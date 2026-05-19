from app.extensions import db
from app.utils.base_model import BaseUUIDModel

class Event(BaseUUIDModel):
    __tablename__ = "events"

    destination_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("destinations.id"), nullable=False)
    attraction_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("attractions.id"), nullable=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    ticket_price = db.Column(db.Float, default=0.0)
    status = db.Column(db.String, default="scheduled")
