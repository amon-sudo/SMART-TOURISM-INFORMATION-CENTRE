from flask import jsonify, request
from marshmallow import ValidationError

from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_repository import (
    ScheduleRepository,
)
from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_schemas import (
    TransportScheduleCreate,
    TransportScheduleResponse,
)


def get_all_schedules_handler():
    try:
        repository = ScheduleRepository()
        schedules = repository.get_all_schedules()
        return jsonify(TransportScheduleResponse.dump(schedules, many=True)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_schedule_handler(schedule_id: str):
    try:
        repository = ScheduleRepository()
        schedule = repository.get_schedule_by_id(schedule_id)
        if schedule:
            return jsonify(TransportScheduleResponse.dump(schedule)), 200
        return jsonify([]), 200
    except ValueError:
        return jsonify({"error": "Invalid schedule_id format. Expected UUID or numeric ID."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_schedule_handler():
    try:
        schedule_data = request.get_json() or {}
        schedule_create = TransportScheduleCreate.load(schedule_data)
        repository = ScheduleRepository()
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
        route_id = request.args.get("route_id")
        departure_time = request.args.get("departure_time")
        arrival_time = request.args.get("arrival_time")
        repository = ScheduleRepository()
        schedules = repository.search_schedules(
            route_id=route_id,
            departure_time=departure_time,
            arrival_time=arrival_time,
        )
        return jsonify(TransportScheduleResponse.dump(schedules, many=True)), 200
    except ValueError:
        return jsonify({"error": "Invalid route_id format. Expected UUID."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_seat_schedule_handler(schedule_id: str):
    try:
        seat_data = request.get_json() or {}
        repository = ScheduleRepository()
        updated_schedule = repository.update_seat_schedule(schedule_id, **seat_data)
        if updated_schedule:
            return jsonify(TransportScheduleResponse.dump(updated_schedule)), 200
        return jsonify({"error": "Schedule not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid schedule_id format. Expected UUID or numeric ID."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_schedule_handler(schedule_id: str):
    try:
        repository = ScheduleRepository()
        success = repository.delete_schedule(schedule_id)
        if success:
            return jsonify({"message": "Schedule deleted successfully"}), 200
        return jsonify({"error": "Schedule not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid schedule_id format. Expected UUID or numeric ID."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500