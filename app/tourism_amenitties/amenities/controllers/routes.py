from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from app.extensions import db

from app.tourism_amenitties.amenities.models.amenities import Amenity
from app.tourism_amenitties.amenities.schemas.amenity import AmenitySchema


amenity_bp = Blueprint(
    "amenity_bp",
    __name__,
    url_prefix="/api/v1/amenities"
)

amenity_schema = AmenitySchema()
amenities_schema = AmenitySchema(many=True)


@amenity_bp.route("/", methods=["POST"])
def create_amenity():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No input data provided"
            }), 400

        errors = amenity_schema.validate(data)

        if errors:
            return jsonify({
                "success": False,
                "errors": errors
            }), 400

        amenity = Amenity(
            name=data["name"],
            icon_url=data.get("icon_url")
        )

        db.session.add(amenity)
        db.session.commit()

        return jsonify({
            "success": True,
            "data": amenity_schema.dump(amenity)
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


@amenity_bp.route("/", methods=["GET"])
def get_amenities():

    try:

        amenities = Amenity.query.all()

        return jsonify({
            "success": True,
            "data": amenities_schema.dump(amenities)
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@amenity_bp.route("/<uuid:id>", methods=["GET"])
def get_amenity(id):

    try:

        amenity = Amenity.query.get(id)

        if not amenity:
            return jsonify({
                "success": False,
                "error": "Amenity not found"
            }), 404

        return jsonify({
            "success": True,
            "data": amenity_schema.dump(amenity)
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@amenity_bp.route("/<uuid:id>", methods=["PATCH"])
def update_amenity(id):

    try:

        amenity = Amenity.query.get(id)

        if not amenity:
            return jsonify({
                "success": False,
                "error": "Amenity not found"
            }), 404

        data = request.get_json()

        allowed_fields = [
            "name",
            "icon_url"
        ]

        for field in allowed_fields:

            if field in data:
                setattr(amenity, field, data[field])

        db.session.commit()

        return jsonify({
            "success": True,
            "data": amenity_schema.dump(amenity)
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@amenity_bp.route("/<uuid:id>", methods=["DELETE"])
def delete_amenity(id):

    try:

        amenity = Amenity.query.get(id)

        if not amenity:
            return jsonify({
                "success": False,
                "error": "Amenity not found"
            }), 404

        db.session.delete(amenity)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Amenity deleted successfully"
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500