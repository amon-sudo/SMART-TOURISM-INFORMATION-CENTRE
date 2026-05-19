from flask import Blueprint

from app.transport_feature.Transport_routes.MVC_architecture.transport_routes_controllers.transport_routes_controllers import (
    create_route_handler,
    delete_route_handler,
    find_active_routes_handler,
    find_routes_near_location_handler,
    get_all_routes_handler,
    get_route_handler,
    update_route_handler,
)

transport_routes_bp = Blueprint("transport_routes", __name__, url_prefix="/routes")


@transport_routes_bp.route("/", methods=["GET"])
def get_all_routes():
    return get_all_routes_handler()


@transport_routes_bp.route("/<string:route_id>", methods=["GET"])
def get_route(route_id):
    return get_route_handler(route_id)


@transport_routes_bp.route("/", methods=["POST"])
def create_route():
    return create_route_handler()


@transport_routes_bp.route("/<string:route_id>", methods=["PUT", "PATCH"])
def update_route(route_id):
    return update_route_handler(route_id)


@transport_routes_bp.route("/<string:route_id>", methods=["DELETE"])
def delete_route(route_id):
    return delete_route_handler(route_id)


@transport_routes_bp.route("/nearby", methods=["GET"])
def find_routes_near_location():
    return find_routes_near_location_handler()


@transport_routes_bp.route("/active", methods=["GET"])
def find_active_routes():
    return find_active_routes_handler()
