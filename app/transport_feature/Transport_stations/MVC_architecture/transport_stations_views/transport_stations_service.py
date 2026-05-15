from uuid import UUID
from typing import List, Dict, Any
from sqlalchemy.orm import session
from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_models.transport_stations_repository import TransportStationRepository


class TransportStationService:

    def __init__(self):
        self.repository = TransportStationRepository()

    @staticmethod
    def _location_to_dict(location_value):
        if not location_value:
            return {"latitude": None, "longitude": None}
        if isinstance(location_value, str) and "," in location_value:
            lat, lon = location_value.split(",", 1)
            try:
                return {"latitude": float(lat), "longitude": float(lon)}
            except ValueError:
                return {"latitude": None, "longitude": None}
        return {"latitude": None, "longitude": None}

    def get_station_details(self, station_id: str) -> Dict[str, Any]:
        """Get detailed information about a transport station, including linked routes and destinations."""
        station = self.repository.get_station_by_id(station_id)
        if not station:
            return {"error": "Station not found"}
        
        station_data = {
            "id": station.id,
            "name": station.name,
            "type": station.type,
            "street": station.street,
            "city": station.city,
            "region": station.region,
            "country": station.country,
            "location": self._location_to_dict(station.location),
            "linked_routes": [route.id for route in station.routes],
            "linked_destinations": [destination.id for destination in station.destinations]
        }
        return station_data
    
    def register_new_station(self, station_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new transport station."""
        try:
            new_station = self.repository.create_station(
                name=station_data.get("name"),
                station_type=station_data.get("type"),
                street=station_data.get("street"),
                city=station_data.get("city"),
                region=station_data.get("region"),
                location=(station_data["location"]["latitude"], station_data["location"]["longitude"]) if station_data.get("location") else None,
                country=station_data.get("country")
            )
            return {"id": new_station.id, "message": "Station created successfully"}
        except Exception as e:
            return {"error": str(e)}
        
    def find_stations_near_location(self, latitude: float, longitude: float, radius_km: float) -> List[Dict[str, Any]]:
        """Find transport stations near a specific location."""
        nearby_stations = self.repository.find_stations_near_location(latitude, longitude, radius_km)
        return [
            {
                "id": station.id,
                "name": station.name,
                "type": station.type,
                "street": station.street,
                "city": station.city,
                "region": station.region,
                "country": station.country,
                "location": self._location_to_dict(station.location),
            }
            for station in nearby_stations
        ]
    
    def link_station_to_routes(self, station_id: str) -> List[Dict[str, Any]]:
        """Get all transport routes linked to a specific station."""
        routes = self.repository.link_to_routes(station_id)
        return [{"id": route.id, "type": route.type} for route in routes]
    
    def link_station_to_destinations(self, station_id: str) -> List[Dict[str, Any]]:
        """Get all destinations linked to a specific station."""
        destinations = self.repository.link_to_destinations(station_id)
        return [{"id": destination.id, "name": destination.name} for destination in destinations]
    
    def update_station(self, station_id: str, station_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing transport station."""
        try:
            updated_station = self.repository.update_station(
                station_id=station_id,
                name=station_data.get("name"),
                station_type=station_data.get("type"),
                street=station_data.get("street"),
                city=station_data.get("city"),
                region=station_data.get("region"),
                location=(station_data["location"]["latitude"], station_data["location"]["longitude"]) if station_data.get("location") else None,
                country=station_data.get("country")
            )
            if updated_station:
                return {"id": updated_station.id, "message": "Station updated successfully"}
            else:
                return {"error": "Station not found"}
        except Exception as e:
            return {"error": str(e)}
        
    def delete_station(self, station_id: str) -> Dict[str, Any]:
        """Delete a transport station."""
        try:
            success = self.repository.delete_station(station_id)
            if success:
                return {"message": "Station deleted successfully"}
            else:
                return {"error": "Station not found"}
        except Exception as e:
            return {"error": str(e)}
        
    def get_stations_by_city(self, city: str) -> List[Dict[str, Any]]:
        """Get all transport stations in a specific city."""
        stations = self.repository.get_stations_by_city(city)
        return [{"id": station.id, "name": station.name} for station in stations]

    def get_stations_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Get all transport stations in a specific region."""
        stations = self.repository.get_stations_by_region(region)
        return [{"id": station.id, "name": station.name} for station in stations]
    
    def get_stations_by_type(self, station_type: str) -> List[Dict[str, Any]]:
        """Get all transport stations of a specific type."""
        stations = self.repository.get_stations_by_type(station_type)
        return [{"id": station.id, "name": station.name} for station in stations]
    
    def get_stations_by_country(self, country: str) -> List[Dict[str, Any]]:
        """Get all transport stations in a specific country."""
        stations = self.repository.get_stations_by_country(country)
        return [{"id": station.id, "name": station.name} for station in stations]
    
    def link_station_to_route(self, station_id: str, route_id: str) -> Dict[str, Any]:
        """Link a transport station to a transport route."""
        try:
            station = self.repository.db.query(transport_station).get(station_id)
            route = self.repository.db.query(transport_route).get(route_id)
            if not station or not route:
                return {"error": "Station or Route not found"}
            station.routes.append(route)
            self.repository.db.commit()
            return {"message": "Station linked to route successfully"}
        except Exception as e:
            return {"error": str(e)}
        
    def link_station_to_destination(self, station_id: str, destination_id: str) -> Dict[str, Any]:
        """Link a transport station to a destination."""
        try:
            station = self.repository.db.query(transport_station).get(station_id)
            destination = self.repository.db.query(Destinations).get(destination_id)
            if not station or not destination:
                return {"error": "Station or Destination not found"}
            station.destinations.append(destination)
            self.repository.db.commit()
            return {"message": "Station linked to destination successfully"}
        except Exception as e:
            return {"error": str(e)}
        