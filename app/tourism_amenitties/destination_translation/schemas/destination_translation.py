

from marshmallow import Schema, fields


class DestinationTranslationSchema(Schema):
    destination_id = fields.UUID(required=True)
    locale = fields.String(required=True)

    name = fields.String(required=True)
    overview = fields.String(allow_none=True)
    culture = fields.String(allow_none=True)
    travel_tips = fields.String(allow_none=True)

    weather_info = fields.Dict(allow_none=True)