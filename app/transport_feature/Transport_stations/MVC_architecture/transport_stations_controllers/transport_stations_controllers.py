from flask import request, jsonify
from marshmallow import ValidationError
#import schemas
from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_models.transport_station_schema import TransportStationCreate, TransportStationUpdate, TransportStationResponse
from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_models.transport_stations_repository import TransportStationRepository

from app.extensions import db


def get_all_stations_handler():
    try:
        repository = TransportStationRepository()
        stations = repository.get_all_stations()
        return jsonify(TransportStationResponse.dump(stations, many=True)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_station_handler():
    try:
        station_data = request.get_json() or {}
        station_create = TransportStationCreate.load(station_data)
        repository = TransportStationRepository()
        new_station = repository.create_station(
            name=station_create["name"],
            station_type=station_create["type"],
            street=station_create.get("street"),
            city=station_create.get("city"),
            region=station_create.get("region"),
            location=(station_create["location"]["latitude"], station_create["location"]["longitude"]) if station_create.get("location") else None,
            country=station_create.get("country"),
        )
        return jsonify(TransportStationResponse.dump(new_station)), 201
    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_station_handler(station_id: str):
        try:
            repository = TransportStationRepository()
            station = repository.get_station_by_id(station_id)
            if station:
                return jsonify(TransportStationResponse.dump(station)), 200
            else:
                return jsonify([]), 200
        except ValueError:
            return jsonify([]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

def link_station_to_routes_handler(station_id: str):
    try:
        repository = TransportStationRepository()
        routes = repository.link_to_routes(station_id)
        response = [{"id": str(route.id), "type": getattr(route, "type", None)} for route in routes]
        return jsonify(response), 200
    except ValueError:
        return jsonify([]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def link_station_to_destinations_handler(station_id: str):
    try:
        repository = TransportStationRepository()
        destinations = repository.link_to_destinations(station_id)
        response = [{"id": str(destination.id), "name": getattr(destination, "name", None)} for destination in destinations]
        return jsonify(response), 200
    except ValueError:
        return jsonify([]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def update_station_handler(station_id: str):
    try:
        station_data = request.get_json() or {}
        station_update = TransportStationUpdate.load(station_data, partial=True)
        repository = TransportStationRepository()
        location = station_update.get("location")
        updated_station = repository.update_station(
            station_id=station_id,
            name=station_update.get("name"),
            station_type=station_update.get("type"),
            street=station_update.get("street"),
            city=station_update.get("city"),
            region=station_update.get("region"),
            location=(location["latitude"], location["longitude"]) if location else None,
            country=station_update.get("country"),
        )
        if updated_station:
            return jsonify(TransportStationResponse.dump(updated_station)), 200
        else:
            return jsonify({"error": "Station not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid station_id format. Expected UUID."}), 400
    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def delete_station_handler(station_id: str):
    try:
        repository = TransportStationRepository()
        success = repository.delete_station(station_id)
        if success:
            return jsonify({"message": "Station deleted successfully"}), 200
        else:
            return jsonify({"error": "Station not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid station_id format. Expected UUID."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def find_stations_near_location_handler():
    try:
        latitude = float(request.args.get("latitude"))
        longitude = float(request.args.get("longitude"))
        radius_km = float(request.args.get("radius_km", 5))  # Default to 5 km if not provided
        repository = TransportStationRepository()
        nearby_stations = repository.find_stations_near_location(latitude, longitude, radius_km)
        response = TransportStationResponse.dump(nearby_stations, many=True)
        return jsonify(response), 200
    except ValueError:
        return jsonify({"error": "Invalid latitude, longitude, or radius_km parameters"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_stations_by_city_handler(city: str):
    try:
        repository = TransportStationRepository()
        stations = repository.get_stations_by_city(city)
        response = TransportStationResponse.dump(stations, many=True)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_stations_by_region_handler(region: str):
    try:
        repository = TransportStationRepository()
        stations = repository.get_stations_by_region(region)
        response = TransportStationResponse.dump(stations, many=True)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_stations_by_type_handler(station_type: str):
    try:
        repository = TransportStationRepository()
        stations = repository.get_stations_by_type(station_type)
        response = TransportStationResponse.dump(stations, many=True)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_stations_by_country_handler(country: str):
    try:
        repository = TransportStationRepository()
        stations = repository.get_stations_by_country(country)
        response = TransportStationResponse.dump(stations, many=True)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_station_handler(station_id: str):
    try:
        repository = TransportStationRepository()
        success = repository.delete_station(station_id)
        if success:
            return jsonify({"message": "Station deleted successfully"}), 200
        else:
            return jsonify({"error": "Station not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid station_id format. Expected UUID."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
