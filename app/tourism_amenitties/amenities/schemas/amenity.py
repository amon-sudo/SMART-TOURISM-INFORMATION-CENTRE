


from marshmallow import Schema, fields


class AmenitySchema(Schema):
    id = fields.UUID(dump_only=True)

    name = fields.String(required=True)
    icon_url = fields.String(allow_none=True)