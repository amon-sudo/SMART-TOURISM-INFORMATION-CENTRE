from app.extensions import db
from app.utils.base_model import BaseUUIDModel

class Accommodation(BaseUUIDModel):
    __tablename__ = "accommodations"

    attraction_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("attractions.id"), nullable=False)
    star_rating = db.Column(db.Integer, default=0)
    check_in_time = db.Column(db.Time)
    check_out_time = db.Column(db.Time)
    policies = db.Column(db.Text)

    attraction = db.relationship("Attraction", backref="accommodation")

class RoomType(BaseUUIDModel):
    __tablename__ = "room_types"

    accommodation_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("accommodations.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, default=1)
    amenities_json = db.Column(db.JSON, default={})

    accommodation = db.relationship("Accommodation", backref="rooms")
