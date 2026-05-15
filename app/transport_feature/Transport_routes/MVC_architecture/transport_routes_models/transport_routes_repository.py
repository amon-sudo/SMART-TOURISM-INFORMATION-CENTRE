from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlalchemy import and_

from app.extensions import db
from app.transport_feature.Transport_routes.MVC_architecture.transport_routes_models.transport_routes_domain import TransportRoute

class TransportRouteRepository:

    def __init__(self):
        self.db = db.session


    
    """Repository class for managing TransportRoute entities in the database."""

    @staticmethod
    def _as_uuid(value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    def create_route(self, type, origin_station_id, duration_minutes, base_fare):
        """Create a new transport route."""
        new_route = TransportRoute(
            id=uuid4(),
            type=type,
            origin_station_id=origin_station_id,
            duration_minutes=duration_minutes,
            base_fare=base_fare,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(new_route)
        db.session.commit()
        return new_route
    

    def get_route_by_id(self, route_id):
        """Retrieve a transport route by its ID."""
        return self.db.get(TransportRoute, self._as_uuid(route_id))

    def get_all_routes(self):
        """Retrieve all transport routes."""
        return self.db.query(TransportRoute).order_by(TransportRoute.created_at.desc()).all()
    
    def find_routes_near_location(self, latitude, longitude, radius_km):
        """Find transport routes that have stations within a certain radius of a given location."""
        # Spatial filtering is disabled for SQLite compatibility.
        return self.db.query(TransportRoute).all()
    
    def find_active_routes(self, origin_station_id: Optional[str] = None, destination_station_id: Optional[str] = None):
        """Find all active transport routes between two stations."""
        query = self.db.query(TransportRoute).filter(TransportRoute.is_active.is_(True))
        if origin_station_id:
            query = query.filter(TransportRoute.origin_station_id == self._as_uuid(origin_station_id))
        # destination_station_id is accepted for API compatibility, but current model has no destination field.
        return query.all()
    
    def update_route(self, route_id, **kwargs):
        """Update an existing transport route."""
        route = self.db.get(TransportRoute, self._as_uuid(route_id))
        if not route:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(route, key):
                setattr(route, key, value)
        route.updated_at = datetime.utcnow()
        db.session.commit()
        return route

    def delete_route(self, route_id):
        """Delete a transport route by its ID."""
        route = self.db.get(TransportRoute, self._as_uuid(route_id))
        if not route:
            return False
        db.session.delete(route)
        db.session.commit()
        return True

    def search_routes(self, origin_station_id=None, _destination_station_id=None, _departure_time=None, _arrival_time=None):
        """Search routes by supported criteria on the current model."""
        query = self.db.query(TransportRoute)
        if origin_station_id:
            query = query.filter(TransportRoute.origin_station_id == self._as_uuid(origin_station_id))
        return query.order_by(TransportRoute.created_at.desc()).all()
    
    



