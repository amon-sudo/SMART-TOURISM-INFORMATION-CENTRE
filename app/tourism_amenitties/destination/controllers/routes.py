from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.extensions import db, cache

from app.tourism_amenitties.destination.models.destination import Destination
from app.tourism_amenitties.destination.schemas.destination import DestinationSchema


destination_bp = Blueprint(
    "destination_bp",
    __name__,
    url_prefix="/api/v1/destinations"
)

destination_schema = DestinationSchema()
destinations_schema = DestinationSchema(many=True)


@destination_bp.route("/", methods=["POST"])
def create_destination():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No input data provided"
            }), 400

        errors = destination_schema.validate(data)

        if errors:
            return jsonify({
                "success": False,
                "errors": errors
            }), 400

        existing_destination = Destination.query.filter_by(
            slug=data["slug"]
        ).first()

        if existing_destination:
            return jsonify({
                "success": False,
                "error": "Slug already exists"
            }), 409

        destination = Destination(
            canonical_name=data["canonical_name"],
            slug=data["slug"]
        )
        # Compatibility with older destinations table shape.
        if hasattr(destination, "name"):
            destination.name = data["canonical_name"]
        if hasattr(destination, "created_at") and destination.created_at is None:
            destination.created_at = datetime.utcnow()
        if hasattr(destination, "updated_at") and destination.updated_at is None:
            destination.updated_at = datetime.utcnow()

        db.session.add(destination)
        db.session.commit()

        cache.clear()

        return jsonify({
            "success": True,
            "data": destination_schema.dump(destination)
        }), 201

    except IntegrityError:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": "Database integrity error"
        }), 400

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@destination_bp.route("/", methods=["GET"])
def get_destinations():

    try:

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        cache_key = f"destinations:{page}:{per_page}"

        cached = cache.get(cache_key)
        if cached:
            return jsonify(cached), 200

        pagination = Destination.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        result = {
            "success": True,
            "data": destinations_schema.dump(pagination.items),
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }

        cache.set(cache_key, result)

        return jsonify(result), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@destination_bp.route("/<uuid:id>", methods=["GET"])
def get_destination(id):

    try:

        cache_key = f"destination:{id}"

        cached = cache.get(cache_key)
        if cached:
            return jsonify(cached), 200

        destination = Destination.query.get(id)

        if not destination:
            return jsonify({
                "success": False,
                "error": "Destination not found"
            }), 404

        result = {
            "success": True,
            "data": destination_schema.dump(destination)
        }

        cache.set(cache_key, result)

        return jsonify(result), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@destination_bp.route("/<uuid:id>", methods=["PATCH"])
def update_destination(id):

    try:

        destination = Destination.query.get(id)

        if not destination:
            return jsonify({
                "success": False,
                "error": "Destination not found"
            }), 404

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No update data provided"
            }), 400

        allowed_fields = [
            "canonical_name",
            "slug"
        ]

        for field in allowed_fields:
            if field in data:
                setattr(destination, field, data[field])

        db.session.commit()

        cache.clear()

        return jsonify({
            "success": True,
            "data": destination_schema.dump(destination)
        }), 200

    except IntegrityError:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": "Slug already exists"
        }), 409

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@destination_bp.route("/<uuid:id>", methods=["DELETE"])
def delete_destination(id):

    try:

        destination = Destination.query.get(id)

        if not destination:
            return jsonify({
                "success": False,
                "error": "Destination not found"
            }), 404

        db.session.delete(destination)
        db.session.commit()

        cache.clear()

        return jsonify({
            "success": True,
            "message": "Destination deleted successfully"
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500