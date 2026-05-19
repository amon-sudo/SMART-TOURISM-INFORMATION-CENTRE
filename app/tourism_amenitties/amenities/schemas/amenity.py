


from marshmallow import Schema, fields


class AmenitySchema(Schema):
    id = fields.UUID(dump_only=True)

    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    icon_url = fields.String(allow_none=True)