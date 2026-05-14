from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from app.extensions import db, cache

from app.tourism_amenitties.amenities.models.amenities import Amenity
from app.tourism_amenitties.amenities.schemas.amenity import AmenitySchema


amenities_bp = Blueprint(
    "amenities_bp",
    __name__,
    url_prefix="/api/v1/amenities"
)

amenity_schema = AmenitySchema()
amenities_schema = AmenitySchema(many=True)


# -------------------------
# CREATE AMENITY (unchanged)
# -------------------------
@amenities_bp.route("/", methods=["POST"])
def create_amenity():

    try:

        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No input data"}), 400

        errors = amenity_schema.validate(data)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        amenity = Amenity(
            name=data["name"],
            icon_url=data.get("icon_url")
        )

        db.session.add(amenity)
        db.session.commit()

        cache.clear()  # simple invalidation for now

        return jsonify({
            "success": True,
            "data": amenity_schema.dump(amenity)
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Integrity error"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------
# GET AMENITIES (REDIS + PAGINATION)
# -------------------------
@amenities_bp.route("/", methods=["GET"])
def get_amenities():

    try:

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        cache_key = f"amenities:list:page:{page}:size:{per_page}"

        cached = cache.get(cache_key)
        if cached:
            return jsonify(cached), 200

        pagination = Amenity.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        response = {
            "success": True,
            "data": amenities_schema.dump(pagination.items),
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }

        cache.set(cache_key, response, timeout=300)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------
# GET SINGLE AMENITY (optional cache)
# -------------------------
@amenities_bp.route("/<uuid:id>", methods=["GET"])
def get_amenity(id):

    try:

        cache_key = f"amenities:detail:{id}"
        cached = cache.get(cache_key)

        if cached:
            return jsonify(cached), 200

        amenity = Amenity.query.get(id)

        if not amenity:
            return jsonify({"success": False, "error": "Not found"}), 404

        response = {
            "success": True,
            "data": amenity_schema.dump(amenity)
        }

        cache.set(cache_key, response, timeout=300)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------
# UPDATE (cache invalidation only)
# -------------------------
@amenities_bp.route("/<uuid:id>", methods=["PATCH"])
def update_amenity(id):

    try:

        amenity = Amenity.query.get(id)

        if not amenity:
            return jsonify({"success": False, "error": "Not found"}), 404

        data = request.get_json()

        if "name" in data:
            amenity.name = data["name"]

        if "icon_url" in data:
            amenity.icon_url = data["icon_url"]

        db.session.commit()

        cache.clear()  # later we improve this

        return jsonify({
            "success": True,
            "data": amenity_schema.dump(amenity)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------
# DELETE
# -------------------------
@amenities_bp.route("/<uuid:id>", methods=["DELETE"])
def delete_amenity(id):

    try:

        amenity = Amenity.query.get(id)

        if not amenity:
            return jsonify({"success": False, "error": "Not found"}), 404

        db.session.delete(amenity)
        db.session.commit()

        cache.clear()

        return jsonify({
            "success": True,
            "message": "Deleted successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500