from flask import Blueprint, jsonify, request

from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_controllers.transport_stations_controllers import (
    get_all_stations_handler,
    create_station_handler,
    delete_station_handler,
    get_station_handler,
    link_station_to_routes_handler,
    link_station_to_destinations_handler,
    update_station_handler
)
from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_models.transport_station_schema import TransportStationResponse
from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_views.transport_stations_service import TransportStationService

transport_stations_bp = Blueprint('transport_stations', __name__, url_prefix='/stations')

#get all stations
@transport_stations_bp.route('/', methods=['GET'])
def get_all_stations():
    return get_all_stations_handler()


@transport_stations_bp.route('/', methods=['POST'])
def create_station():
    return create_station_handler()

@transport_stations_bp.route('/<string:station_id>', methods=['GET'])
def get_station(station_id):
    return get_station_handler(station_id)

@transport_stations_bp.route('/<string:station_id>/routes', methods=['GET'])
def link_station_to_routes(station_id):
    return link_station_to_routes_handler(station_id)

@transport_stations_bp.route('/<string:station_id>/destinations', methods=['GET'])
def link_station_to_destinations(station_id):
    return link_station_to_destinations_handler(station_id)

@transport_stations_bp.route('/nearby', methods=['GET'])
def find_stations_near_location():
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    radius_km = request.args.get('radius_km', type=float, default=5.0)
    if latitude is None or longitude is None:
        return jsonify({"error": "Latitude and longitude are required parameters"}), 400
    service = TransportStationService()
    nearby_stations = service.find_stations_near_location(latitude, longitude, radius_km)
    response = TransportStationResponse.dump(nearby_stations, many=True)
    return jsonify(response), 200   


@transport_stations_bp.route('/search', methods=['GET'])
def search_stations():
    city = request.args.get('city')
    region = request.args.get('region')
    station_type = request.args.get('type')
    country = request.args.get('country')
    
    service = TransportStationService()
    if city:
        stations = service.get_stations_by_city(city)
    elif region:
        stations = service.get_stations_by_region(region)
    elif station_type:
        stations = service.get_stations_by_type(station_type)
    elif country:
        stations = service.get_stations_by_country(country)
    else:
        return jsonify({"error": "At least one search parameter (city, region, type, country) is required"}), 400
    
    response = TransportStationResponse.dump(stations, many=True)
    return jsonify(response), 200

@transport_stations_bp.route('/<string:station_id>', methods=['PUT', 'PATCH'])
def update_station(station_id):
    return update_station_handler(station_id)

@transport_stations_bp.route('/<string:station_id>', methods=['DELETE'])
def delete_station(station_id):
    return delete_station_handler(station_id)




