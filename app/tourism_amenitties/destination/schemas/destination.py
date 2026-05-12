

from marshmallow import Schema, fields


class DestinationSchema(Schema):
    id = fields.UUID(dump_only=True)

    canonical_name = fields.String(required=True)
    slug = fields.String(required=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)