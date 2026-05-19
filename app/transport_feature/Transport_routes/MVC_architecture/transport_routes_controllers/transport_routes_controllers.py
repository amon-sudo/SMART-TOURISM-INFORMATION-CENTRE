from flask import jsonify, request
from marshmallow import ValidationError

from app.transport_feature.Transport_routes.MVC_architecture.transport_routes_models.transport_routes_repository import (
    TransportRouteRepository,
)
from app.transport_feature.Transport_routes.MVC_architecture.transport_routes_models.transport_routes_schemas import (
    TransportRouteCreate,
    TransportRouteUpdate,
    TransportRoutesResponse,
)


def _route_to_dict(route):
    return TransportRoutesResponse.dump(route)


def get_all_routes_handler():
    try:
        repository = TransportRouteRepository()
        routes = repository.get_all_routes()
        return jsonify([_route_to_dict(route) for route in routes]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_route_handler(route_id: str):
    try:
        repository = TransportRouteRepository()
        route = repository.get_route_by_id(route_id)
        if not route:
            return jsonify([]), 200
        return jsonify(_route_to_dict(route)), 200
    except ValueError:
        return jsonify([]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_route_handler():
    try:
        payload = request.get_json() or {}
        route_create = TransportRouteCreate.load(payload)
        repository = TransportRouteRepository()
        new_route = repository.create_route(
            type=route_create["type"],
            origin_station_id=route_create["origin_station_id"],
            duration_minutes=route_create["duration_minutes"],
            base_fare=route_create["base_fare"],
        )
        return jsonify(_route_to_dict(new_route)), 201
    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_route_handler(route_id: str):
    try:
        payload = request.get_json() or {}
        route_update = TransportRouteUpdate.load(payload, partial=True)
        repository = TransportRouteRepository()
        updated_route = repository.update_route(
            route_id=route_id,
            **route_update,
        )
        if not updated_route:
            return jsonify({"error": "Route not found"}), 404
        return jsonify(_route_to_dict(updated_route)), 200
    except ValueError:
        return jsonify({"error": "Invalid route_id format. Expected UUID."}), 400
    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_route_handler(route_id: str):
    try:
        repository = TransportRouteRepository()
        success = repository.delete_route(route_id)
        if not success:
            return jsonify({"error": "Route not found"}), 404
        return jsonify({"message": "Route deleted successfully"}), 200
    except ValueError:
        return jsonify({"error": "Invalid route_id format. Expected UUID."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def find_routes_near_location_handler():
    try:
        latitude = request.args.get("latitude", type=float)
        longitude = request.args.get("longitude", type=float)
        radius_km = request.args.get("radius_km", type=float, default=5.0)
        if latitude is None or longitude is None:
            return jsonify({"error": "Latitude and longitude are required parameters"}), 400
        repository = TransportRouteRepository()
        nearby_routes = repository.find_routes_near_location(latitude, longitude, radius_km)
        response = [_route_to_dict(route) for route in nearby_routes]
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def find_active_routes_handler():
    try:
        origin_station_id = request.args.get("origin_station_id")
        destination_station_id = request.args.get("destination_station_id")
        repository = TransportRouteRepository()
        active_routes = repository.find_active_routes(origin_station_id, destination_station_id)
        response = [_route_to_dict(route) for route in active_routes]
        return jsonify(response), 200
    except ValueError:
        return jsonify([]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
