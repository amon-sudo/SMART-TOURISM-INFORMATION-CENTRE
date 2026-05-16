from flask import Blueprint, request
from app.tourism_amenitties.events.services.service import EventService, TourPackageService
from app.tourism_amenitties.events.schemas import EventSchema, TourPackageSchema
from app.utils.responses import ApiResponse
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)
tourism_bp = Blueprint("tourism_bp", __name__)

event_schema = EventSchema()
tour_schema = TourPackageSchema()

@tourism_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json() or {}
    errors = event_schema.validate(data)
    if errors:
        return ApiResponse.error(message="Validation failed", details=errors, status_code=422)
    try:
        event = EventService.create(data)
        return ApiResponse.success(data=event_schema.dump(event), status_code=201)
    except IntegrityError:
        return ApiResponse.error(message="Invalid destination_id or attraction_id: referenced resource does not exist", status_code=400)
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return ApiResponse.error(message="Internal error", status_code=500)

@tourism_bp.route("/tours", methods=["POST"])
def create_tour():
    data = request.get_json() or {}
    errors = tour_schema.validate(data)
    if errors:
        return ApiResponse.error(message="Validation failed", details=errors, status_code=422)
    try:
        tour = TourPackageService.create(data)
        return ApiResponse.success(data=tour_schema.dump(tour), status_code=201)
    except IntegrityError:
        return ApiResponse.error(message="Invalid operator_id: referenced business profile does not exist", status_code=400)
    except Exception as e:
        logger.error(f"Error creating tour: {e}")
        return ApiResponse.error(message="Internal error", status_code=500)
