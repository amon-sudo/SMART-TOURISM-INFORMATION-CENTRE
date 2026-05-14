from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from app.extensions import db

from app.tourism_amenitties.attraction_amenities.models.attraction_amenities import AttractionAmenity

from app.tourism_amenitties.attraction_amenities.schemas.attraction_amenity import AttractionAmenitySchema


attraction_amenity_bp = Blueprint(
    "attraction_amenity_bp",
    __name__,
    url_prefix="/api/v1/attraction-amenities"
)

attraction_amenity_schema = AttractionAmenitySchema()
attraction_amenities_schema = AttractionAmenitySchema(many=True)


@attraction_amenity_bp.route("/", methods=["POST"])
def create_attraction_amenity():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No input data provided"
            }), 400

        errors = attraction_amenity_schema.validate(data)

        if errors:
            return jsonify({
                "success": False,
                "errors": errors
            }), 400

        existing_relation = AttractionAmenity.query.filter_by(
            attraction_id=data["attraction_id"],
            amenity_id=data["amenity_id"]
        ).first()

        if existing_relation:
            return jsonify({
                "success": False,
                "error": "Relationship already exists"
            }), 409

        attraction_amenity = AttractionAmenity(
            attraction_id=data["attraction_id"],
            amenity_id=data["amenity_id"]
        )

        db.session.add(attraction_amenity)
        db.session.commit()

        return jsonify({
            "success": True,
            "data": attraction_amenity_schema.dump(attraction_amenity)
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


@attraction_amenity_bp.route("/", methods=["GET"])
def get_attraction_amenities():

    try:

        relationships = AttractionAmenity.query.all()

        return jsonify({
            "success": True,
            "data": attraction_amenities_schema.dump(relationships)
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@attraction_amenity_bp.route(
    "/<uuid:attraction_id>/<uuid:amenity_id>",
    methods=["DELETE"]
)
def delete_attraction_amenity(attraction_id, amenity_id):

    try:

        relationship = AttractionAmenity.query.filter_by(
            attraction_id=attraction_id,
            amenity_id=amenity_id
        ).first()

        if not relationship:
            return jsonify({
                "success": False,
                "error": "Relationship not found"
            }), 404

        db.session.delete(relationship)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Relationship deleted successfully"
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500