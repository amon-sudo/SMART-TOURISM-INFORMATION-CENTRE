from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
import uuid

from app.extensions import db

from app.tourism_amenitties.destination_translation.models.destination_translation import DestinationTranslation
from app.tourism_amenitties.destination_translation.schemas.destination_translation import DestinationTranslationSchema


destination_translation_bp = Blueprint(
    "destination_translation_bp",
    __name__,
    url_prefix="/api/v1/destination-translations"
)

translation_schema = DestinationTranslationSchema()
translations_schema = DestinationTranslationSchema(many=True)


@destination_translation_bp.route("/", methods=["POST"])
def create_destination_translation():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No input data provided"
            }), 400

        errors = translation_schema.validate(data)

        if errors:
            return jsonify({
                "success": False,
                "errors": errors
            }), 400

        existing_translation = DestinationTranslation.query.filter_by(
            destination_id=uuid.UUID(str(data["destination_id"])),
            locale=data["locale"]
        ).first()

        if existing_translation:
            return jsonify({
                "success": False,
                "error": "Translation already exists for this locale"
            }), 409

        translation = DestinationTranslation(
            destination_id=uuid.UUID(str(data["destination_id"])),
            locale=data["locale"],
            name=data["name"],
            overview=data.get("overview"),
            culture=data.get("culture"),
            travel_tips=data.get("travel_tips"),
            weather_info=data.get("weather_info")
        )

        db.session.add(translation)
        db.session.commit()

        return jsonify({
            "success": True,
            "data": translation_schema.dump(translation)
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


@destination_translation_bp.route("/", methods=["GET"])
def get_destination_translations():

    try:

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        destination_id = request.args.get("destination_id")
        locale = request.args.get("locale")

        query = DestinationTranslation.query

        if destination_id:
            query = query.filter_by(destination_id=destination_id)

        if locale:
            query = query.filter_by(locale=locale)

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return jsonify({
            "success": True,
            "data": translations_schema.dump(pagination.items),
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@destination_translation_bp.route(
    "/<uuid:destination_id>/<string:locale>",
    methods=["GET"]
)
def get_destination_translation(destination_id, locale):

    try:

        translation = DestinationTranslation.query.filter_by(
            destination_id=destination_id,
            locale=locale
        ).first()

        if not translation:
            return jsonify({
                "success": False,
                "error": "Translation not found"
            }), 404

        return jsonify({
            "success": True,
            "data": translation_schema.dump(translation)
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@destination_translation_bp.route(
    "/<uuid:destination_id>/<string:locale>",
    methods=["PATCH"]
)
def update_destination_translation(destination_id, locale):

    try:

        translation = DestinationTranslation.query.filter_by(
            destination_id=destination_id,
            locale=locale
        ).first()

        if not translation:
            return jsonify({
                "success": False,
                "error": "Translation not found"
            }), 404

        data = request.get_json()

        allowed_fields = [
            "name",
            "overview",
            "culture",
            "travel_tips",
            "weather_info"
        ]

        for field in allowed_fields:
            if field in data:
                setattr(translation, field, data[field])

        db.session.commit()

        return jsonify({
            "success": True,
            "data": translation_schema.dump(translation)
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@destination_translation_bp.route(
    "/<uuid:destination_id>/<string:locale>",
    methods=["DELETE"]
)
def delete_destination_translation(destination_id, locale):

    try:

        translation = DestinationTranslation.query.filter_by(
            destination_id=destination_id,
            locale=locale
        ).first()

        if not translation:
            return jsonify({
                "success": False,
                "error": "Translation not found"
            }), 404

        db.session.delete(translation)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Translation deleted successfully"
        }), 200

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500