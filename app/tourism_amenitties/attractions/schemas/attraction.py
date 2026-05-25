


from marshmallow import Schema, fields, EXCLUDE


class AttractionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.UUID(dump_only=True)

    destination_id = fields.UUID(required=True)
    business_owner_id = fields.UUID(required=True)

    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    image_url = fields.String(allow_none=True)
    media_urls = fields.List(fields.String(), allow_none=True, load_default=None)
    category = fields.String(allow_none=True)

    location = fields.Raw(allow_none=True)  # PostGIS geography
    latitude = fields.Float(allow_none=True, dump_only=True)
    longitude = fields.Float(allow_none=True, dump_only=True)
    destination_name = fields.Method("get_destination_name", dump_only=True)

    avg_rating = fields.Float(dump_only=True)
    status = fields.String(allow_none=True)

    is_wheelchair_accessible = fields.Boolean()
    entry_fee = fields.Float(allow_none=True)
    view_count = fields.Integer(dump_only=True)

    # Kenya administrative location
    county = fields.String(allow_none=True)
    sub_county = fields.String(allow_none=True)
    ward = fields.String(allow_none=True)
    locality = fields.String(allow_none=True)
    gps_coordinates = fields.String(allow_none=True)
    tourism_type = fields.String(allow_none=True)

    # Experience highlights
    unique_features = fields.String(allow_none=True)
    environmental_impact = fields.String(allow_none=True)
    visitor_capacity = fields.Integer(allow_none=True)
    types_of_experiences = fields.String(allow_none=True)
    avg_time_spent = fields.String(allow_none=True)
    best_visiting_periods = fields.String(allow_none=True)
    key_events = fields.String(allow_none=True)

    # Situational analysis
    roads_condition = fields.String(allow_none=True)
    visitor_center_info = fields.String(allow_none=True)
    water_supply = fields.String(allow_none=True)
    signage_info = fields.String(allow_none=True)
    fencing_security = fields.String(allow_none=True)
    parking_area = fields.String(allow_none=True)
    rest_areas = fields.String(allow_none=True)
    site_current_status = fields.String(allow_none=True)

    # Associated services
    tour_operators = fields.String(allow_none=True)
    nearby_accommodation = fields.String(allow_none=True)
    distance_to_major_town = fields.String(allow_none=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_destination_name(self, obj):
        if obj.destination:
            return obj.destination.name or obj.destination.canonical_name or obj.destination.slug
        return None