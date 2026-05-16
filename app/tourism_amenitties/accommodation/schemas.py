from marshmallow import Schema, fields

class AccommodationSchema(Schema):
    id = fields.UUID(dump_only=True)
    attraction_id = fields.UUID(required=True)
    star_rating = fields.Int()
    check_in_time = fields.Time()
    check_out_time = fields.Time()
    policies = fields.Str()

class RoomTypeSchema(Schema):
    id = fields.UUID(dump_only=True)
    accommodation_id = fields.UUID(required=True)
    name = fields.Str(required=True)
    base_price = fields.Float(required=True)
    capacity = fields.Int()
    amenities_json = fields.Dict()
