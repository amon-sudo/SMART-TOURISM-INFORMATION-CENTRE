



from marshmallow import Schema, fields


class AttractionAmenitySchema(Schema):
    attraction_id = fields.UUID(required=True)
    amenity_id = fields.UUID(required=True)