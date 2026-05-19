from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
import uuid

from app.extensions import db, cache

from app.tourism_amenitties.attraction_translations.models.attraction_tran import AttractionTranslation
from app.tourism_amenitties.attraction_translations.schemas.attraction_translation import AttractionTranslationSchema


attraction_translation_bp = Blueprint("attraction_translation_bp", __name__)

translation_schema = AttractionTranslationSchema()
translations_schema = AttractionTranslationSchema(many=True)


@attraction_translation_bp.route("/", methods=["POST"])
def create_attraction_translation():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No input data provided"}), 400

        errors = translation_schema.validate(data)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        existing_translation = AttractionTranslation.query.filter_by(
            attraction_id=uuid.UUID(str(data["attraction_id"])),
            locale=data["locale"]
        ).first()

        if existing_translation:
            return jsonify({"success": False, "error": "Translation already exists for this locale"}), 409

        translation = AttractionTranslation(
            attraction_id=uuid.UUID(str(data["attraction_id"])),
            locale=data["locale"],
            name=data["name"],
            description=data.get("description"),
            tips=data.get("tips")
        )

        db.session.add(translation)
        db.session.commit()

        cache.clear()

        return jsonify({
            "success": True,
            "data": translation_schema.dump(translation)
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "error": "Database integrity error"}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@attraction_translation_bp.route("/", methods=["GET"])
def get_attraction_translations():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        attraction_id = request.args.get("attraction_id")
        locale = request.args.get("locale")

        cache_key = f"att_translations:p:{page}:pp:{per_page}:aid:{attraction_id}:loc:{locale}"
        cached = cache.get(cache_key)

        if cached:
            return jsonify(cached), 200

        query = AttractionTranslation.query

        if attraction_id:
            query = query.filter_by(attraction_id=attraction_id)

        if locale:
            query = query.filter_by(locale=locale)

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        response = {
            "success": True,
            "data": translations_schema.dump(pagination.items),
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


@attraction_translation_bp.route("/<uuid:attraction_id>/<string:locale>", methods=["GET"])
def get_attraction_translation(attraction_id, locale):
    try:
        cache_key = f"att_translation:{attraction_id}:{locale}"
        cached = cache.get(cache_key)

        if cached:
            return jsonify(cached), 200

        translation = AttractionTranslation.query.filter_by(
            attraction_id=attraction_id,
            locale=locale
        ).first()

        if not translation:
            return jsonify({"success": False, "error": "Translation not found"}), 404

        response = {
            "success": True,
            "data": translation_schema.dump(translation)
        }

        cache.set(cache_key, response, timeout=300)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@attraction_translation_bp.route("/<uuid:attraction_id>/<string:locale>", methods=["PATCH"])
def update_attraction_translation(attraction_id, locale):
    try:
        translation = AttractionTranslation.query.filter_by(
            attraction_id=attraction_id,
            locale=locale
        ).first()

        if not translation:
            return jsonify({"success": False, "error": "Translation not found"}), 404

        data = request.get_json()

        allowed_fields = ["name", "description", "tips"]

        for field in allowed_fields:
            if field in data:
                setattr(translation, field, data[field])

        db.session.commit()

        cache.clear()

        return jsonify({
            "success": True,
            "data": translation_schema.dump(translation)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@attraction_translation_bp.route("/<uuid:attraction_id>/<string:locale>", methods=["DELETE"])
def delete_attraction_translation(attraction_id, locale):
    try:
        translation = AttractionTranslation.query.filter_by(
            attraction_id=attraction_id,
            locale=locale
        ).first()

        if not translation:
            return jsonify({"success": False, "error": "Translation not found"}), 404

        db.session.delete(translation)
        db.session.commit()

        cache.clear()

        return jsonify({
            "success": True,
            "message": "Translation deleted successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500