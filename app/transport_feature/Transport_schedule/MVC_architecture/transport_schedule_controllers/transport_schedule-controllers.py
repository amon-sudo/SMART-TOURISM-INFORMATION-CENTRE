from flask import request, jsonify
from marshmallow import ValidationError
from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_schemas import TransportScheduleCreate, TransportScheduleResponse
from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_repository import ScheduleRepository
from app.extensions import db


TransportScheduleRepository = ScheduleRepository

def get_schedule_handler(schedule_id: str):
    try:
        repository = TransportScheduleRepository()
        schedule = repository.get_schedule_by_id(schedule_id)
        if schedule:
            return jsonify(TransportScheduleResponse.dump(schedule)), 200
        else:
            return jsonify({"error": "Schedule not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def create_schedule_handler():
    try:
        schedule_data = request.get_json() or {}
        schedule_create = TransportScheduleCreate.load(schedule_data)
        repository = TransportScheduleRepository()
        new_schedule = repository.create_schedule(
            transport_route_id=schedule_create["transport_route_id"],
            departure_time=schedule_create["departure_time"],
            arrival_time=schedule_create["arrival_time"],
            available_seats=schedule_create["available_seats"],
            price=schedule_create["price"],
        )
        return jsonify(TransportScheduleResponse.dump(new_schedule)), 201
    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def search_schedules_handler():
    try:
        route_id = request.args.get('route_id')
        departure_time = request.args.get('departure_time')
        arrival_time = request.args.get('arrival_time')
        repository = TransportScheduleRepository()
        schedules = repository.search_schedules(route_id=route_id, departure_time=departure_time, arrival_time=arrival_time)
        response = TransportScheduleResponse.dump(schedules, many=True)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def update_seat_schedule_handler(schedule_id: str):
    try:
        seat_data = request.get_json()
        repository = TransportScheduleRepository()
        updated_schedule = repository.update_seat_schedule(schedule_id, **seat_data)
        if updated_schedule:
            return jsonify(TransportScheduleResponse.dump(updated_schedule)), 200
        else:
            return jsonify({"error": "Schedule not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def delete_schedule_handler(schedule_id: str):
    try:
        repository = TransportScheduleRepository()
        success = repository.delete_schedule(schedule_id)
        if success:
            return jsonify({"message": "Schedule deleted successfully"}), 200
        else:
            return jsonify({"error": "Schedule not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_schedules_by_route_handler(route_id: str):
    try:
        repository = TransportScheduleRepository()
        schedules = repository.get_schedules_by_route(route_id)
        response = TransportScheduleResponse.dump(schedules, many=True)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_schedules_by_departure_time_handler():
    try:
        departure_time = request.args.get('departure_time')
        repository = TransportScheduleRepository()
        schedules = repository.get_schedules_by_departure_time(departure_time)
        response = TransportScheduleResponse.dump(schedules, many=True)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def get_schedules_by_arrival_time_handler():
    try:
        arrival_time = request.args.get('arrival_time')
        repository = TransportScheduleRepository()
        schedules = repository.get_schedules_by_arrival_time(arrival_time)
        response = TransportScheduleResponse.dump(schedules, many=True)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
