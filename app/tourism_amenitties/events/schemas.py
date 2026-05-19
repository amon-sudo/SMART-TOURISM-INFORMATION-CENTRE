from marshmallow import Schema, fields

class EventSchema(Schema):
    id = fields.UUID(dump_only=True)
    destination_id = fields.UUID(required=True)
    attraction_id = fields.UUID(required=False)
    name = fields.Str(required=True)
    description = fields.Str()
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    ticket_price = fields.Float()
    status = fields.Str()

class TourPackageSchema(Schema):
    id = fields.UUID(dump_only=True)
    operator_id = fields.UUID(required=True)
    name = fields.Str(required=True)
    description = fields.Str()
    duration_days = fields.Int(required=True)
    price = fields.Float(required=True)
    max_participants = fields.Int()
    status = fields.Str()
