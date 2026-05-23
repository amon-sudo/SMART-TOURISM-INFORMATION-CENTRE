from flask import Blueprint, request, jsonify
from app.extensions import db
from app.culture_hub.models.culture_hub import CultureHub
from app.kiosk_feature.kiosk.middleware.require_admin import admin_required

culture_hub_bp = Blueprint("culture_hub", __name__, url_prefix="/api/v1/culture-hubs")


@culture_hub_bp.route("/", methods=["GET"])
def list_culture_hubs():
    county = request.args.get("county")
    status = request.args.get("status", "active")
    q = CultureHub.query
    if county:
        q = q.filter(CultureHub.county.ilike(f"%{county}%"))
    if status != "all":
        q = q.filter(CultureHub.status == status)
    hubs = q.order_by(CultureHub.county, CultureHub.name).all()
    return jsonify({"data": [h.to_dict() for h in hubs]}), 200


@culture_hub_bp.route("/<uuid:hub_id>", methods=["GET"])
def get_culture_hub(hub_id):
    hub = CultureHub.query.get_or_404(str(hub_id))
    return jsonify({"data": hub.to_dict()}), 200


@culture_hub_bp.route("/", methods=["POST"])
@admin_required
def create_culture_hub():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("county"):
        return jsonify({"error": "name and county are required"}), 400
    hub = CultureHub(
        name=data["name"],
        county=data["county"],
        sub_county=data.get("sub_county"),
        ward=data.get("ward"),
        locality=data.get("locality"),
        description=data.get("description"),
        tourism_type=data.get("tourism_type"),
        community_role=data.get("community_role"),
        community_benefits=data.get("community_benefits"),
        community_enterprises=data.get("community_enterprises"),
        activities=data.get("activities"),
        unique_features=data.get("unique_features"),
        environmental_impact=data.get("environmental_impact"),
        visitor_capacity=data.get("visitor_capacity"),
        best_visiting_periods=data.get("best_visiting_periods"),
        key_events=data.get("key_events"),
        image_url=data.get("image_url"),
        media_urls=data.get("media_urls"),
        status=data.get("status", "active"),
        contact_info=data.get("contact_info"),
    )
    db.session.add(hub)
    db.session.commit()
    return jsonify({"data": hub.to_dict()}), 201


@culture_hub_bp.route("/<uuid:hub_id>", methods=["PATCH"])
@admin_required
def update_culture_hub(hub_id):
    hub = CultureHub.query.get_or_404(str(hub_id))
    data = request.get_json(silent=True) or {}
    updatable = [
        "name", "county", "sub_county", "ward", "locality", "description",
        "tourism_type", "community_role", "community_benefits", "community_enterprises",
        "activities", "unique_features", "environmental_impact", "visitor_capacity",
        "best_visiting_periods", "key_events", "image_url", "media_urls", "status",
        "contact_info",
    ]
    for field in updatable:
        if field in data:
            setattr(hub, field, data[field])
    db.session.commit()
    return jsonify({"data": hub.to_dict()}), 200


@culture_hub_bp.route("/<uuid:hub_id>", methods=["DELETE"])
@admin_required
def delete_culture_hub(hub_id):
    hub = CultureHub.query.get_or_404(str(hub_id))
    db.session.delete(hub)
    db.session.commit()
    return jsonify({"message": "Culture hub deleted"}), 200
