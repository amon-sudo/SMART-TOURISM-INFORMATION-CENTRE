from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import func

from app.extensions import db
from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_domain import (
    transport_schedule,
)


class ScheduleRepository:
    def __init__(self):
        self.db = db.session

    @staticmethod
    def _as_uuid(value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @staticmethod
    def _parse_schedule_identifier(value):
        if value is None:
            raise ValueError("schedule_id is required")
        if isinstance(value, UUID):
            return "uuid", value

        value_str = str(value).strip()
        if value_str.isdigit():
            return "numeric", int(value_str)

        return "uuid", UUID(value_str)

    def _find_schedule(self, schedule_id) -> Optional[transport_schedule]:
        identifier_type, identifier_value = self._parse_schedule_identifier(schedule_id)
        if identifier_type == "numeric":
            return (
                self.db.query(transport_schedule)
                .filter(transport_schedule.numeric_id == identifier_value)
                .first()
            )
        return self.db.get(transport_schedule, identifier_value)

    def get_schedule_by_id(self, schedule_id: UUID) -> Optional[transport_schedule]:
        return self._find_schedule(schedule_id)

    def get_all_schedules(self):
        return self.db.query(transport_schedule).order_by(transport_schedule.departure_time.asc()).all()

    def create_schedule(
        self,
        transport_route_id: UUID,
        departure_time: datetime,
        arrival_time: datetime,
        available_seats: int,
        price: float,
    ) -> transport_schedule:
        max_numeric_id = self.db.query(func.max(transport_schedule.numeric_id)).scalar()
        next_numeric_id = (max_numeric_id or 0) + 1

        new_schedule = transport_schedule(
            numeric_id=next_numeric_id,
            transport_route_id=transport_route_id,
            departure_time=departure_time,
            arrival_time=arrival_time,
            available_seats=available_seats,
            price=price,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(new_schedule)
        self.db.commit()
        self.db.refresh(new_schedule)
        return new_schedule

    def search_schedules(self, route_id=None, departure_time=None, arrival_time=None):
        query = self.db.query(transport_schedule).filter(transport_schedule.is_active.is_(True))
        if route_id:
            query = query.filter(transport_schedule.transport_route_id == self._as_uuid(route_id))
        if departure_time:
            query = query.filter(transport_schedule.departure_time >= departure_time)
        if arrival_time:
            query = query.filter(transport_schedule.arrival_time <= arrival_time)
        return query.order_by(transport_schedule.departure_time.asc()).all()

    def update_seat_schedule(self, schedule_id: UUID, **kwargs) -> Optional[transport_schedule]:
        schedule = self._find_schedule(schedule_id)
        if not schedule:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(schedule, key):
                setattr(schedule, key, value)
        schedule.updated_at = datetime.utcnow()
        self.db.commit()
        return schedule

    def delete_schedule(self, schedule_id: UUID) -> bool:
        schedule = self._find_schedule(schedule_id)
        if not schedule:
            return False
        self.db.delete(schedule)
        self.db.commit()
        return True

    def get_schedules_by_route(self, route_id):
        return self.db.query(transport_schedule).filter(transport_schedule.transport_route_id == self._as_uuid(route_id)).all()

    def get_schedules_by_departure_time(self, departure_time):
        return self.db.query(transport_schedule).filter(transport_schedule.departure_time >= departure_time).all()

    def get_schedules_by_arrival_time(self, arrival_time):
        return self.db.query(transport_schedule).filter(transport_schedule.arrival_time <= arrival_time).all()