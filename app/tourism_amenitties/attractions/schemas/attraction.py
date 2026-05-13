


from marshmallow import Schema, fields


class AttractionSchema(Schema):
    id = fields.UUID(dump_only=True)

    destination_id = fields.UUID(required=True)
    business_owner_id = fields.UUID(required=True)

    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    category = fields.String(allow_none=True)

    location = fields.Raw(allow_none=True)  # PostGIS geography

    avg_rating = fields.Float(dump_only=True)
    status = fields.String(allow_none=True)

    is_wheelchair_accessible = fields.Boolean()
    entry_fee = fields.Float(allow_none=True)
    view_count = fields.Integer(dump_only=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)