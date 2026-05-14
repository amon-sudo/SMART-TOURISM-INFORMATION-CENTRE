from uuid import UUID
from typing import List, Dict, Any
from sqlalchemy.orm import session

from app.transport_feature.Transport_routes.MVC_architecture.transport_routes_models.transport_routes_repository import TransportRouteRepository

class TransportRouteService:
    
    def __init__(self):
        self.repository = TransportRouteRepository()

    def get_route_details(self, route_id: UUID) -> Dict[str, Any]:
        """Get detailed information about a transport route, including linked stations."""
        route = self.repository.get_route_by_id(route_id)
        if not route:
            return {"error": "Route not found"}
        
        route_data = {
            "id": route.id,
            "type": route.type,
            "origin_station_id": route.origin_station_id,
            "duration_minutes": route.duration_minutes,
            "base_fare": route.base_fare,
            "created_at": route.created_at.isoformat(),
            "updated_at": route.updated_at.isoformat(),
            "linked_stations": [station.id for station in route.stations]
        }
        return route_data
    
    def register_new_route(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new transport route."""
        try:
            new_route = self.repository.create_route(
                type=route_data.get("type"),
                origin_station_id=route_data.get("origin_station_id"),
                duration_minutes=route_data.get("duration_minutes"),
                base_fare=route_data.get("base_fare")
            )
            return {"id": new_route.id, "message": "Route created successfully"}
        except Exception as e:
            return {"error": str(e)}
        
    def find_routes_near_location(self, latitude: float, longitude: float, radius_km: float) -> List[Dict[str, Any]]:
        """Find transport routes near a specific location."""
        nearby_routes = self.repository.find_routes_near_location(latitude, longitude, radius_km)
        return [
            {
                "id": route.id,
                "type": route.type,
                "origin_station_id": route.origin_station_id,
                "duration_minutes": route.duration_minutes,
                "base_fare": route.base_fare,
                "created_at": route.created_at.isoformat(),
                "updated_at": route.updated_at.isoformat()
            }
            for route in nearby_routes
        ]
    
    def find_active_routes(self, origin_station_id: UUID, destination_station_id: UUID) -> List[Dict[str, Any]]:
        """Find active transport routes between two stations."""
        active_routes = self.repository.find_active_routes(origin_station_id, destination_station_id)
        return [
            {
                "id": route.id,
                "type": route.type,
                "origin_station_id": route.origin_station_id,
                "duration_minutes": route.duration_minutes,
                "base_fare": route.base_fare,
                "created_at": route.created_at.isoformat(),
                "updated_at": route.updated_at.isoformat()
            }
            for route in active_routes
        ]
    
    def update_route(self, route_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing transport route."""
        try:
            updated_route = self.repository.update_route(route_id, **update_data)
            if updated_route:
                return {
                    "id": updated_route.id,
                    "type": updated_route.type,
                    "origin_station_id": updated_route.origin_station_id,
                    "duration_minutes": updated_route.duration_minutes,
                    "base_fare": updated_route.base_fare,
                    "created_at": updated_route.created_at.isoformat(),
                    "updated_at": updated_route.updated_at.isoformat()
                }
            else:
                return {"error": "Route not found"}
        except Exception as e:
            return {"error": str(e)}
        
    def cancel_route(self, route_id: UUID) -> Dict[str, Any]:
        """Cancel a transport route."""
        try:
            success = self.repository.delete_route(route_id)
            if success:
                return {"message": "Route cancelled successfully"}
            else:
                return {"error": "Route not found"}
        except Exception as e:
            return {"error": str(e)}    
        
    def search_routes(self, origin_station_id: UUID, destination_station_id: UUID, departure_time: str, arrival_time: str) -> List[Dict[str, Any]]:
        """Search for transport routes based on criteria."""
        try:
            routes = self.repository.search_routes(origin_station_id, destination_station_id, departure_time, arrival_time)
            return [
                {
                    "id": route.id,
                    "type": route.type,
                    "origin_station_id": route.origin_station_id,
                    "duration_minutes": route.duration_minutes,
                    "base_fare": route.base_fare,
                    "created_at": route.created_at.isoformat(),
                    "updated_at": route.updated_at.isoformat()
                }
                for route in routes
            ]
        except Exception as e:
            return {"error": str(e)}
        
        