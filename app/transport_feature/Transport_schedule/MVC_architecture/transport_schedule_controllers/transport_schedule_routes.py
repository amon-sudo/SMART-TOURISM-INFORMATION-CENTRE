from flask import Blueprint, jsonify, request
from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_controllers.transport_schedule_controllers import (
    get_all_schedules_handler,
    get_schedule_handler,
    create_schedule_handler,
    search_schedules_handler,
    update_seat_schedule_handler,
    delete_schedule_handler,
)

transport_schedule_bp = Blueprint('transport_schedule', __name__, url_prefix='/schedules')

#get all schedules
@transport_schedule_bp.route('/all_schedules', methods=['GET'])
def get_all_schedules():
    return get_all_schedules_handler()


@transport_schedule_bp.route('/<string:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    return get_schedule_handler(schedule_id)

@transport_schedule_bp.route('/add_schedule', methods=['POST'])
def create_schedule():
    return create_schedule_handler()


@transport_schedule_bp.route('/search', methods=['GET'])
def search_schedules():
    return search_schedules_handler()

@transport_schedule_bp.route('/<string:schedule_id>/update_seats', methods=['PUT'])
def update_seat_schedule(schedule_id):
    return update_seat_schedule_handler(schedule_id)

@transport_schedule_bp.route('/<string:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    return delete_schedule_handler(schedule_id)


