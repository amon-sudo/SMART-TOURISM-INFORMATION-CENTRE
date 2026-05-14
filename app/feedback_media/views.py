# app/feedback_media/views.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.extensions import db
from .schemas import ReviewSchema, MediaGallerySchema, EmergencyContactSchema
from .services import (
    create_review,
    add_media,
    add_contact,
    list_reviews,
    list_media,
    list_contacts,
)
from app.feedback_media.models import User  # <-- make sure User model exists

feedback_bp = Blueprint("feedback_media", __name__, url_prefix="/api/v1/feedback")


def error_response(code, error, message=None, details=None):
    payload = {"error": error}
    if message:
        payload["message"] = message
    if details:
        payload["details"] = details
    return jsonify(payload), code


def _int_arg(name, default):
    try:
        return int(request.args.get(name, default))
    except (TypeError, ValueError):
        return default


# -------------------------
# Users endpoints
# -------------------------
from sqlalchemy.exc import IntegrityError

@feedback_bp.route("/users", methods=["POST"])
def create_user_route():
    payload = request.get_json(force=True)
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        return error_response(400, "validation_error", "Email and password required")

    try:
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response(400, "duplicate_email", "Email already exists")
    except Exception:
        current_app.logger.exception("Failed to create user")
        return error_response(500, "internal_server_error", "Failed to create user")

    return jsonify({"id": str(user.id), "email": user.email}), 201


@feedback_bp.route("/users", methods=["GET"])
def list_users_route():
    users = User.query.all()
    data = [{"id": str(u.id), "email": u.email} for u in users]
    return jsonify(data), 200


@feedback_bp.route("/users/<uuid:user_id>", methods=["GET"])
def get_user_route(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response(404, "not_found", "User not found")
    return jsonify({"id": str(user.id), "email": user.email}), 200


@feedback_bp.route("/users/<uuid:user_id>", methods=["PUT"])
def update_user_route(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response(404, "not_found", "User not found")

    payload = request.get_json(force=True)
    if "email" in payload:
        user.email = payload["email"]
    if "password" in payload:
        user.set_password(payload["password"])
    db.session.commit()
    return jsonify({"id": str(user.id), "email": user.email}), 200


@feedback_bp.route("/users/<uuid:user_id>", methods=["DELETE"])
def delete_user_route(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response(404, "not_found", "User not found")
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200


# -------------------------
# Reviews endpoints
# -------------------------
@feedback_bp.route("/reviews", methods=["POST"])
@jwt_required()
def create_review_route():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return error_response(400, "validation_error", "JSON payload required")

    tourist_id = get_jwt_identity()
    if not tourist_id:
        return error_response(401, "unauthorized", "Missing JWT identity")
    payload["tourist_id"] = tourist_id

    try:
        data = ReviewSchema().load(payload)
    except ValidationError as err:
        return error_response(400, "validation_error", details=err.messages)

    try:
        review = create_review(data)
    except Exception:
        current_app.logger.exception("Failed to create review")
        return error_response(500, "internal_server_error", "Failed to create review")

    result = ReviewSchema().dump(review)
    return jsonify(result), 201


@feedback_bp.route("/reviews", methods=["GET"])
def list_reviews_route():
    page = _int_arg("page", 1)
    per_page = _int_arg("per_page", 20)
    filters = {
        "target_type": request.args.get("target_type"),
        "target_id": request.args.get("target_id"),
        "tourist_id": request.args.get("tourist_id"),
        "status": request.args.get("status"),
    }

    try:
        items = list_reviews(filters, page=page, per_page=per_page)
    except Exception:
        current_app.logger.exception("Failed to list reviews")
        return error_response(500, "internal_server_error", "Failed to list reviews")

    if hasattr(items, "items"):
        data = ReviewSchema(many=True).dump(items.items)
        meta = {
            "page": items.page,
            "per_page": items.per_page,
            "total": items.total,
            "pages": items.pages,
        }
        return jsonify({"data": data, "meta": meta}), 200

    data = ReviewSchema(many=True).dump(items)
    return jsonify(data), 200


# -------------------------
# Media endpoints
# -------------------------
@feedback_bp.route("/gallery", methods=["POST"])
@jwt_required()
def add_media_route():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return error_response(400, "validation_error", "JSON payload required")

    try:
        data = MediaGallerySchema().load(payload)
    except ValidationError as err:
        return error_response(400, "validation_error", details=err.messages)

    try:
        media = add_media(data)
    except Exception:
        current_app.logger.exception("Failed to add media")
        return error_response(500, "internal_server_error", "Failed to add media")

    result = MediaGallerySchema().dump(media)
    return jsonify(result), 201


@feedback_bp.route("/gallery", methods=["GET"])
def list_media_route():
    target_type = request.args.get("target_type")
    target_id = request.args.get("target_id")

    try:
        items = list_media(target_type=target_type, target_id=target_id)
    except Exception:
        current_app.logger.exception("Failed to list media")
        return error_response(500, "internal_server_error", "Failed to list media")

    data = MediaGallerySchema(many=True).dump(items)
    return jsonify(data), 200


# -------------------------
# Contacts endpoints
# -------------------------
@feedback_bp.route("/contacts", methods=["POST"])
@jwt_required()
def add_contact_route():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return error_response(400, "validation_error", "JSON payload required")

    try:
        data = EmergencyContactSchema().load(payload)
    except ValidationError as err:
        return error_response(400, "validation_error", details=err.messages)

    try:
        contact = add_contact(data)
    except Exception:
        current_app.logger.exception("Failed to add contact")
        return error_response(500, "internal_server_error", "Failed to add contact")

    result = EmergencyContactSchema().dump(contact)
    return jsonify(result), 201


@feedback_bp.route("/contacts", methods=["GET"])
def list_contacts_route():
    destination_id = request.args.get("destination_id")

    try:
        items = list_contacts(destination_id=destination_id)
    except Exception:
        current_app.logger.exception("Failed to list contacts")
        return error_response(500, "internal_server_error", "Failed to list contacts")

    result = []
    for c in items:
        obj = EmergencyContactSchema().dump(c)
        if hasattr(c, "location") and c.location is not None:
            try:
                wkt = db.session.scalar(db.func.ST_AsText(c.location))
                obj["location"] = wkt
            except Exception:
                try:
                    obj["location"] = str(c.location)
                except Exception:
                    obj["location"] = None
        result.append(obj)

    return jsonify(result), 200
from app.feedback_media.models import Destination

@feedback_bp.route("/destinations", methods=["POST"])
def create_destination_route():
    payload = request.get_json(force=True)
    name = payload.get("name")
    description = payload.get("description")
    if not name:
        return error_response(400, "validation_error", "Name required")

    try:
        dest = Destination(name=name, description=description)
        db.session.add(dest)
        db.session.commit()
    except Exception:
        current_app.logger.exception("Failed to create destination")
        return error_response(500, "internal_server_error", "Failed to create destination")

    return jsonify({"id": str(dest.id), "name": dest.name, "description": dest.description}), 201


@feedback_bp.route("/destinations", methods=["GET"])
def list_destinations_route():
    items = Destination.query.all()
    data = [{"id": str(d.id), "name": d.name, "description": d.description} for d in items]
    return jsonify(data), 200

# destinatio

@feedback_bp.route("/destinations/<uuid:dest_id>", methods=["GET"])
def get_destination_route(dest_id):
    dest = Destination.query.get(dest_id)
    if not dest:
        return error_response(404, "not_found", "Destination not found")
    return jsonify({"id": str(dest.id), "name": dest.name, "description": dest.description}), 200


@feedback_bp.route("/destinations/<uuid:dest_id>", methods=["PUT"])
def update_destination_route(dest_id):
    dest = Destination.query.get(dest_id)
    if not dest:
        return error_response(404, "not_found", "Destination not found")

    payload = request.get_json(force=True)
    if "name" in payload:
        dest.name = payload["name"]
    if "description" in payload:
        dest.description = payload["description"]
    db.session.commit()
    return jsonify({"id": str(dest.id), "name": dest.name, "description": dest.description}), 200


@feedback_bp.route("/destinations/<uuid:dest_id>", methods=["DELETE"])
def delete_destination_route(dest_id):
    dest = Destination.query.get(dest_id)
    if not dest:
        return error_response(404, "not_found", "Destination not found")
    db.session.delete(dest)
    db.session.commit()
    return jsonify({"message": "Destination deleted"}), 200