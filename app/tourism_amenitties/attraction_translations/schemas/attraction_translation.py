


from marshmallow import Schema, fields


class AttractionTranslationSchema(Schema):
    attraction_id = fields.UUID(required=True)
    locale = fields.String(required=True)

    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    tips = fields.String(allow_none=True)