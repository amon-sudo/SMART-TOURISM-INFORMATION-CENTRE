from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
import uuid

from app.extensions import db, cache

from app.tourism_amenitties.attractions.models.attraction import Attraction
from app.tourism_amenitties.attractions.schemas.attraction import AttractionSchema


attraction_bp = Blueprint(
    "attraction_bp",
    __name__,
    url_prefix="/api/v1/attractions"
)

attraction_schema = AttractionSchema()
attractions_schema = AttractionSchema(many=True)


@attraction_bp.route("/", methods=["POST"])
def create_attraction():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No input data provided"
            }), 400

        errors = attraction_schema.validate(data)

        if errors:
            return jsonify({
                "success": False,
                "errors": errors
            }), 400

        attraction = Attraction(
            destination_id=uuid.UUID(str(data["destination_id"])),
            business_owner_id=uuid.UUID(str(data["business_owner_id"])),
            name=data["name"],
            description=data.get("description"),
            category=data.get("category"),
            status=data.get("status"),
            is_wheelchair_accessible=data.get("is_wheelchair_accessible", False),
            entry_fee=data.get("entry_fee")
        )

        db.session.add(attraction)
        db.session.commit()

        # clear cache after write
        cache.clear()

        return jsonify({
            "success": True,
            "data": attraction_schema.dump(attraction)
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


@attraction_bp.route("/", methods=["GET"])
def get_attractions():

    try:

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        # Public/tourist listing must only ever show approved attractions
        # (STORY001, STORY028). Admin endpoints use their own listing.
        include_all = request.args.get("include_all") == "true"

        cache_key = f"attractions_page_{page}_per_page_{per_page}_all_{include_all}"

        # 1. check redis first
        cached_data = cache.get(cache_key)
        if cached_data:
            return jsonify(cached_data), 200

        # 2. query DB
        query = Attraction.query
        if not include_all:
            query = query.filter(Attraction.status == "approved")
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        response = {
            "success": True,
            "data": attractions_schema.dump(pagination.items),
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_pages": pagination.pages,
                "total_items": pagination.total
            }
        }

        # 3. store in redis
        cache.set(cache_key, response, timeout=300)

        return jsonify(response), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@attraction_bp.route("/<uuid:id>", methods=["GET"])
def get_attraction(id):

    try:

        attraction = Attraction.query.get(id)

        if not attraction:
            return jsonify({
                "success": False,
                "error": "Attraction not found"
            }), 404

        return jsonify({
            "success": True,
            "data": attraction_schema.dump(attraction)
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@attraction_bp.route("/<uuid:id>", methods=["PATCH"])
def update_attraction(id):

    try:

        attraction = Attraction.query.get(id)

        if not attraction:
            return jsonify({
                "success": False,
                "error": "Attraction not found"
            }), 404

        data = request.get_json()

        allowed_fields = [
            "name",
            "description",
            "category",
            "status",
            "entry_fee",
            "is_wheelchair_accessible"
        ]

        for field in allowed_fields:
            if field in data:
                setattr(attraction, field, data[field])

        db.session.commit()

        # clear cache after update
        cache.clear()

        return jsonify({
            "success": True,
            "data": attraction_schema.dump(attraction)
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@attraction_bp.route("/<uuid:id>", methods=["DELETE"])
def delete_attraction(id):

    try:

        attraction = Attraction.query.get(id)

        if not attraction:
            return jsonify({
                "success": False,
                "error": "Attraction not found"
            }), 404

        db.session.delete(attraction)
        db.session.commit()

        # clear cache after delete
        cache.clear()

        return jsonify({
            "success": True,
            "message": "Attraction deleted successfully"
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500