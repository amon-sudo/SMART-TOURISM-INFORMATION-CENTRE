


from marshmallow import Schema, fields


class AttractionSchema(Schema):
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

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_destination_name(self, obj):
        if obj.destination:
            return obj.destination.name or obj.destination.canonical_name or obj.destination.slug
        return None