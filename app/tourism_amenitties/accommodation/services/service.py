from app.extensions import db
from app.tourism_amenitties.accommodation.models.accommodation import Accommodation, RoomType

class AccommodationService:
    @staticmethod
    def create_accommodation(data):
        accommodation = Accommodation(**data)
        db.session.add(accommodation)
        db.session.commit()
        return accommodation

    @staticmethod
    def add_room(data):
        room = RoomType(**data)
        db.session.add(room)
        db.session.commit()
        return room

    @staticmethod
    def get_all():
        return Accommodation.query.all()
