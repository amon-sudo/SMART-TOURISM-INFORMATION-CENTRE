from flask import Blueprint


def create_transport_feature_blueprint():
    from app.transport_feature.Transport_routes.MVC_architecture.transport_routes_controllers.transport_routes_route import (
        transport_routes_bp,
    )
    from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_controllers.transport_schedule_routes import (
        transport_schedule_bp,
    )
    from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_controllers.transport_stations_routes import (
        transport_stations_bp,
    )

    blueprint = Blueprint("transport_feature", __name__, url_prefix="/api/v1/transport")
    blueprint.register_blueprint(transport_routes_bp)
    blueprint.register_blueprint(transport_schedule_bp)
    blueprint.register_blueprint(transport_stations_bp)
    return blueprint

    
    