"""Compatibility package for legacy `app.models` imports.

Re-exports models from their feature-module homes so that older code that
references ``from app.models import X`` continues to work. Add new entries
here as the consolidation progresses.
"""

from app.tourism_amenitties.attractions.models.attraction import Attraction  # noqa: F401
from app.tourism_amenitties.accommodation.models.accommodation import Accommodation  # noqa: F401
from app.tourism_amenitties.tours.models.tour_package import TourPackage  # noqa: F401
# Transport models reference each other via string-based relationships, so
# they all need to be loaded into the SQLAlchemy registry together.
from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_models.transport_stations_domain import (  # noqa: F401
    transport_station as TransportStation,
)
from app.transport_feature.Transport_routes.MVC_architecture.transport_routes_models.transport_routes_domain import (  # noqa: F401
    TransportRoute,
)
from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_domain import (
    transport_schedule as TransportSchedule,  # noqa: F401
)

__all__ = [
    "Attraction",
    "Accommodation",
    "TourPackage",
    "TransportSchedule",
]
