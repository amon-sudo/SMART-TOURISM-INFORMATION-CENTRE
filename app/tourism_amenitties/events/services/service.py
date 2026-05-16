from app.extensions import db
from app.tourism_amenitties.events.models.event import Event
from app.tourism_amenitties.tours.models.tour_package import TourPackage

class EventService:
    @staticmethod
    def create(data):
        event = Event(**data)
        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def get_all():
        return Event.query.all()

class TourPackageService:
    @staticmethod
    def create(data):
        tour = TourPackage(**data)
        db.session.add(tour)
        db.session.commit()
        return tour

    @staticmethod
    def get_all():
        return TourPackage.query.all()
