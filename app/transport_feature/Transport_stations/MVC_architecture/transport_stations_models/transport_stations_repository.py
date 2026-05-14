from typing import Optional
from uuid import UUID

from app.extensions import db
from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_models.transport_stations_domain import (
    transport_station,
)


class TransportStationRepository:

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
    def _serialize_location(location):
        if not location:
            return None
        lat, lon = location
        return f"{lat},{lon}"

    def get_station_by_id(self, station_id: str) -> Optional[transport_station]:
        """Retrieve a transport station by its ID."""
        return self.db.get(transport_station, self._as_uuid(station_id))

    def get_all_stations(self):
        """Retrieve all transport stations."""
        return self.db.query(transport_station).order_by(transport_station.name.asc()).all()
    
    def find_stations_near_location(self, latitude: float, longitude: float, radius_km: float):
        """Find transport stations within a certain radius of a given location."""
        # Spatial filtering is disabled for SQLite compatibility.
        return self.db.query(transport_station).all()
    
    def link_to_routes(self, station_id: str):
        """Find all transport routes that are linked to a specific station."""
        station = self.db.get(transport_station, self._as_uuid(station_id))
        if station:
            return getattr(station, "routes", [])
        return []
    
    def link_to_destinations(self, station_id: str):
        """Find all destinations that are linked to a specific station."""
        station = self.db.get(transport_station, self._as_uuid(station_id))
        if station:
            return getattr(station, "destinations", [])
        return []
    
    def get_stations_by_city(self, city: str):
        """Retrieve all transport stations in a specific city."""
        return self.db.query(transport_station).filter(transport_station.city == city).all()
    
    def get_stations_by_region(self, region: str):
        """Retrieve all transport stations in a specific region."""
        return self.db.query(transport_station).filter(transport_station.region == region).all()
    
    def get_stations_by_type(self, station_type: str):
        """Retrieve all transport stations of a specific type."""
        return self.db.query(transport_station).filter(transport_station.type == station_type).all()
    
    def get_stations_by_country(self, country: str):
        """Retrieve all transport stations in a specific country."""
        return self.db.query(transport_station).filter(transport_station.country == country).all()
    
    def create_station(self, name: str, station_type: str, street: Optional[str], city: Optional[str], region: Optional[str], location: Optional[tuple], country: Optional[str]) -> transport_station:
        """Create a new transport station."""
        new_station = transport_station(
            name=name,
            type=station_type,
            street=street,
            city=city,
            region=region,
            location=self._serialize_location(location),
            country=country
        )
        self.db.add(new_station)
        self.db.commit()
        return new_station
    
    def update_station(self, station_id: str, **kwargs) -> Optional[transport_station]:
        """Update an existing transport station."""
        station = self.db.get(transport_station, self._as_uuid(station_id))
        if not station:
            return None
        for key, value in kwargs.items():
            if value is None:
                continue
            if key == "station_type":
                setattr(station, "type", value)
            elif key == "location" and value is not None:
                setattr(station, key, self._serialize_location(value))
            else:
                setattr(station, key, value)
        self.db.commit()
        return station

    def delete_station(self, station_id: str) -> bool:
        station = self.db.get(transport_station, self._as_uuid(station_id))
        if not station:
            return False
        self.db.delete(station)
        self.db.commit()
        return True
    