from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from app.extensions import db

from app.tourism_amenitties.attraction_translations.models.attraction_tran import AttractionTranslation

from app.tourism_amenitties.attraction_translations.schemas.attraction_translation import AttractionTranslationSchema


attraction_translation_bp = Blueprint(
    "attraction_translation_bp",
    __name__,
    url_prefix="/api/v1/attraction-translations"
)

translation_schema = AttractionTranslationSchema()
translations_schema = AttractionTranslationSchema(many=True)


@attraction_translation_bp.route("/", methods=["POST"])
def create_attraction_translation():

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

        existing_translation = AttractionTranslation.query.filter_by(
            attraction_id=data["attraction_id"],
            locale=data["locale"]
        ).first()

        if existing_translation:
            return jsonify({
                "success": False,
                "error": "Translation already exists for this locale"
            }), 409

        translation = AttractionTranslation(
            attraction_id=data["attraction_id"],
            locale=data["locale"],
            name=data["name"],
            description=data.get("description"),
            tips=data.get("tips")
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


@attraction_translation_bp.route("/", methods=["GET"])
def get_attraction_translations():

    try:

        translations = AttractionTranslation.query.all()

        return jsonify({
            "success": True,
            "data": translations_schema.dump(translations)
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@attraction_translation_bp.route(
    "/<uuid:attraction_id>/<string:locale>",
    methods=["GET"]
)
def get_attraction_translation(attraction_id, locale):

    try:

        translation = AttractionTranslation.query.filter_by(
            attraction_id=attraction_id,
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


@attraction_translation_bp.route(
    "/<uuid:attraction_id>/<string:locale>",
    methods=["PATCH"]
)
def update_attraction_translation(attraction_id, locale):

    try:

        translation = AttractionTranslation.query.filter_by(
            attraction_id=attraction_id,
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
            "description",
            "tips"
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


@attraction_translation_bp.route(
    "/<uuid:attraction_id>/<string:locale>",
    methods=["DELETE"]
)
def delete_attraction_translation(attraction_id, locale):

    try:

        translation = AttractionTranslation.query.filter_by(
            attraction_id=attraction_id,
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