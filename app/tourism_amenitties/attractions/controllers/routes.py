from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
import uuid

from app.extensions import db, cache

from app.tourism_amenitties.attractions.models.attraction import Attraction
from app.tourism_amenitties.attractions.schemas.attraction import AttractionSchema


attraction_bp = Blueprint("attraction_bp", __name__)

attraction_schema = AttractionSchema()
attractions_schema = AttractionSchema(many=True)


def _bust_attractions_cache() -> None:
    """Increment the generation counter so all cached attraction list keys miss."""
    gen = cache.get("attractions_cache_gen") or 0
    cache.set("attractions_cache_gen", gen + 1, timeout=0)


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

        media_urls = data.get("media_urls") or []
        # First media URL doubles as the cover image_url if not provided separately.
        cover = data.get("image_url") or (media_urls[0] if media_urls else None)

        attraction = Attraction(
            destination_id=uuid.UUID(str(data["destination_id"])),
            business_owner_id=uuid.UUID(str(data["business_owner_id"])),
            name=data["name"],
            description=data.get("description"),
            image_url=cover,
            media_urls=media_urls,
            category=data.get("category"),
            status=data.get("status"),
            is_wheelchair_accessible=data.get("is_wheelchair_accessible", False),
            entry_fee=data.get("entry_fee")
        )

        db.session.add(attraction)
        db.session.commit()

        _bust_attractions_cache()

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
        category = request.args.get("category", "").strip() or None
        destination_id = request.args.get("destination_id", "").strip() or None
        search = request.args.get("search", "").strip() or None

        # Cache key encodes all filter dimensions so different queries get
        # independent cache entries.
        gen = cache.get("attractions_cache_gen") or 0
        cache_key = (
            f"attractions_gen_{gen}_p{page}_pp{per_page}_all{include_all}"
            f"_cat{category}_dest{destination_id}_q{search}"
        )

        # 1. check redis first
        cached_data = cache.get(cache_key)
        if cached_data:
            return jsonify(cached_data), 200

        # 2. query DB
        query = Attraction.query.options(joinedload(Attraction.destination))
        if not include_all:
            query = query.filter(Attraction.status == "approved")
        if category:
            query = query.filter(Attraction.category == category)
        if destination_id:
            try:
                query = query.filter(Attraction.destination_id == uuid.UUID(destination_id))
            except ValueError:
                return jsonify({"success": False, "error": "Invalid destination_id format"}), 400
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(Attraction.name.ilike(like), Attraction.description.ilike(like))
            )

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
                "total_items": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
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

        attraction = (
            Attraction.query
            .options(joinedload(Attraction.destination))
            .get(id)
        )

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
            "image_url",
            "media_urls",
            "category",
            "status",
            "entry_fee",
            "is_wheelchair_accessible"
        ]

        for field in allowed_fields:
            if field in data:
                setattr(attraction, field, data[field])

        # Keep image_url in sync: if media_urls were updated, use the first as cover.
        if "media_urls" in data and data["media_urls"] and "image_url" not in data:
            attraction.image_url = data["media_urls"][0]

        db.session.commit()

        _bust_attractions_cache()

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

        _bust_attractions_cache()

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