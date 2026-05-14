from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from app.extensions import db

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
            destination_id=data["destination_id"],
            business_owner_id=data["business_owner_id"],
            name=data["name"],
            description=data.get("description"),
            category=data.get("category"),
            status=data.get("status"),
            is_wheelchair_accessible=data.get(
                "is_wheelchair_accessible",
                False
            ),
            entry_fee=data.get("entry_fee")
        )

        db.session.add(attraction)
        db.session.commit()

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

        attractions = Attraction.query.all()

        return jsonify({
            "success": True,
            "data": attractions_schema.dump(attractions)
        }), 200

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