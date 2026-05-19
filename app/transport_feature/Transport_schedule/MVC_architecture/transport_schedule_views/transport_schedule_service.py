from uuid import UUID
from app.extensions import db
from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_repository import transport_schedule
from datetime import datetime, timedelta
from sqlalchemy. orm import session
from typing import List, Dict, Any


class TransportScheduleService:
    
    def __init__(self):
        self.repository = ScheduleRepository()

    def get_schedule_details(self, schedule_id: UUID) -> Dict[str, Any]:
        """Get detailed information about a transport schedule."""
        schedule = self.repository.get_schedule_by_id(schedule_id)
        if not schedule:
            return {"error": "Schedule not found"}
        
        schedule_data = {
            "id": schedule.id,
            "transport_route_id": schedule.transport_route_id,
            "departure_time": schedule.departure_time.isoformat(),
            "arrival_time": schedule.arrival_time.isoformat(),
            "available_seats": schedule.available_seats,
            "price": schedule.price,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat()
        }
        return schedule_data
    
    def register_new_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new transport schedule."""
        try:
            new_schedule = self.repository.create_schedule(
                transport_route_id=schedule_data.get("transport_route_id"),
                departure_time=datetime.fromisoformat(schedule_data.get("departure_time")),
                arrival_time=datetime.fromisoformat(schedule_data.get("arrival_time")),
                available_seats=schedule_data.get("available_seats"),
                price=schedule_data.get("price")
            )
            return {"id": new_schedule.id, "message": "Schedule created successfully"}
        except Exception as e:
            return {"error": str(e)}
        
    def search_schedules(self, route_id: Optional[UUID] = None, departure_time: Optional[datetime] = None, arrival_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Search for transport schedules based on criteria."""
        schedules = self.repository.search_schedules(route_id=route_id, departure_time=departure_time, arrival_time=arrival_time)
        return [
            {
                "id": schedule.id,
                "transport_route_id": schedule.transport_route_id,
                "departure_time": schedule.departure_time.isoformat(),
                "arrival_time": schedule.arrival_time.isoformat(),
                "available_seats": schedule.available_seats,
                "price": schedule.price,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
            for schedule in schedules
        ]
    
    def publish_schedule(self, schedule_id: UUID) -> Dict[str, Any]:
        """Publish a transport schedule, making it active and available for booking."""
        try:
            updated_schedule = self.repository.update_seat_schedule(schedule_id, is_active=True)
            if not updated_schedule:
                return {"error": "Schedule not found"}
            return {"id": updated_schedule.id, "message": "Schedule published successfully"}
        except Exception as e:
            return {"error": str(e)}
        
    def query_any_available_schedules(self, route_id: Optional[UUID] = None, departure_time: Optional[datetime] = None, arrival_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Query for any available schedules based on criteria."""
        schedules = self.repository.search_schedules(route_id=route_id, departure_time=departure_time, arrival_time=arrival_time)
        return [
            {
                "id": schedule.id,
                "transport_route_id": schedule.transport_route_id,
                "departure_time": schedule.departure_time.isoformat(),
                "arrival_time": schedule.arrival_time.isoformat(),
                "available_seats": schedule.available_seats,
                "price": schedule.price,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
            for schedule in schedules
        ]   
    
    def process_seat_booking(self, schedule_id: UUID, seats_to_book: int) -> Dict[str, Any]:
        """Process a seat booking for a transport schedule."""
        try:
            updated_schedule = self.repository.update_seat_schedule(schedule_id, available_seats=seats_to_book)
            if not updated_schedule:
                return {"error": "Schedule not found or not enough available seats"}
            return {
                "id": updated_schedule.id,
                "available_seats": updated_schedule.available_seats,
                "message": f"Successfully booked {seats_to_book} seats"
            }
        except Exception as e:
            return {"error": str(e)}
        
    def cancel_schedule(self, schedule_id: UUID) -> Dict[str, Any]:
        """Cancel a transport schedule."""
        try:
            updated_schedule = self.repository.update_seat_schedule(schedule_id, is_active=False)
            if not updated_schedule:
                return {"error": "Schedule not found"}
            return {"id": updated_schedule.id, "message": "Schedule cancelled successfully"}
        except Exception as e:
            return {"error": str(e)}
        
    def delete_schedule(self, schedule_id: UUID) -> Dict[str, Any]:
        """Delete a transport schedule."""
        try:
            success = self.repository.delete_schedule(schedule_id)
            if success:
                return {"message": "Schedule deleted successfully"}
            else:
                return {"error": "Schedule not found"}
        except Exception as e:
            return {"error": str(e)}
        
    def get_schedules_by_route(self, route_id: UUID) -> List[Dict[str, Any]]:
        """Get all schedules for a specific transport route."""
        schedules = self.repository.search_schedules(route_id=route_id)
        return [
            {
                "id": schedule.id,
                "transport_route_id": schedule.transport_route_id,
                "departure_time": schedule.departure_time.isoformat(),
                "arrival_time": schedule.arrival_time.isoformat(),
                "available_seats": schedule.available_seats,
                "price": schedule.price,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
            for schedule in schedules
        ]
    
    def get_schedules_by_departure_time(self, departure_time: datetime) -> List[Dict[str, Any]]:
        """Get all schedules departing at a specific time."""
        schedules = self.repository.search_schedules(departure_time=departure_time)
        return [
            {
                "id": schedule.id,
                "transport_route_id": schedule.transport_route_id,
                "departure_time": schedule.departure_time.isoformat(),
                "arrival_time": schedule.arrival_time.isoformat(),
                "available_seats": schedule.available_seats,
                "price": schedule.price,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
            for schedule in schedules
        ]
    
    def get_schedules_by_arrival_time(self, arrival_time: datetime) -> List[Dict[str, Any]]:
        """Get all schedules arriving at a specific time."""
        schedules = self.repository.search_schedules(arrival_time=arrival_time)
        return [
            {
                "id": schedule.id,
                "transport_route_id": schedule.transport_route_id,
                "departure_time": schedule.departure_time.isoformat(),
                "arrival_time": schedule.arrival_time.isoformat(),
                "available_seats": schedule.available_seats,
                "price": schedule.price,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
            for schedule in schedules
        ]
    def get_schedules_by_price_range(self, min_price: float, max_price: float) -> List[Dict[str, Any]]:
        """Get all schedules within a specific price range."""
        schedules = self.repository.search_schedules(price_range=(min_price, max_price))
        return [
            {
                "id": schedule.id,
                "transport_route_id": schedule.transport_route_id,
                "departure_time": schedule.departure_time.isoformat(),
                "arrival_time": schedule.arrival_time.isoformat(),
                "available_seats": schedule.available_seats,
                "price": schedule.price,
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            }
            for schedule in schedules
        ]
    