from flask import Blueprint, request
from app.tourism_amenitties.accommodation.services.service import AccommodationService
from app.tourism_amenitties.accommodation.schemas import AccommodationSchema, RoomTypeSchema
from app.utils.responses import ApiResponse
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)
accommodation_bp = Blueprint("accommodation_bp", __name__)

acc_schema = AccommodationSchema()
room_schema = RoomTypeSchema()

@accommodation_bp.route("/", methods=["POST"])
# @jwt_required()
def create():
    data = request.get_json() or {}
    errors = acc_schema.validate(data)
    if errors:
        return ApiResponse.error(message="Invalid data", details=errors, status_code=422)
    
    try:
        acc = AccommodationService.create_accommodation(data)
        return ApiResponse.success(data=acc_schema.dump(acc), status_code=201)
    except IntegrityError:
        return ApiResponse.error(message="Invalid attraction_id: referenced resource does not exist", status_code=400)
    except Exception as e:
        logger.error(f"Error creating accommodation: {e}")
        return ApiResponse.error(message="Internal error", status_code=500)

@accommodation_bp.route("/room", methods=["POST"])
def add_room():
    data = request.get_json() or {}
    errors = room_schema.validate(data)
    if errors:
        return ApiResponse.error(message="Invalid data", details=errors, status_code=422)
    
    try:
        room = AccommodationService.add_room(data)
        return ApiResponse.success(data=room_schema.dump(room), status_code=201)
    except Exception as e:
        logger.error(f"Error adding room: {e}")
        return ApiResponse.error(message="Internal error", status_code=500)
