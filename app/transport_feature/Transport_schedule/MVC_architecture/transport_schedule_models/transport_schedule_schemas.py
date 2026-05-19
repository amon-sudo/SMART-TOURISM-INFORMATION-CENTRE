from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class TransportScheduleSchema(Schema):
    departure_time = fields.DateTime(required=True)
    arrival_time = fields.DateTime(required=True)
    available_seats = fields.Integer(required=True, validate=validate.Range(min=0))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    is_active = fields.Boolean(load_default=True)

    @validates_schema
    def validate_arrival_after_departure(self, data, **kwargs):
        departure_time = data.get("departure_time")
        arrival_time = data.get("arrival_time")
        if departure_time and arrival_time and arrival_time <= departure_time:
            raise ValidationError(
                {"arrival_time": ["Arrival time must be after departure time"]}
            )


class TransportScheduleCreateSchema(TransportScheduleSchema):
    transport_route_id = fields.UUID(required=True)


class TransportScheduleUpdateSchema(Schema):
    departure_time = fields.DateTime(required=False)
    arrival_time = fields.DateTime(required=False)
    available_seats = fields.Integer(required=False, validate=validate.Range(min=0))
    price = fields.Float(required=False, validate=validate.Range(min=0))
    is_active = fields.Boolean(required=False)

    @validates_schema
    def validate_arrival_after_departure(self, data, **kwargs):
        departure_time = data.get("departure_time")
        arrival_time = data.get("arrival_time")
        if departure_time and arrival_time and arrival_time <= departure_time:
            raise ValidationError(
                {"arrival_time": ["Arrival time must be after departure time"]}
            )


class TransportScheduleResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    numeric_id = fields.Integer(dump_only=True)
    transport_route_id = fields.UUID(dump_only=True)
    departure_time = fields.DateTime(dump_only=True)
    arrival_time = fields.DateTime(dump_only=True)
    available_seats = fields.Integer(dump_only=True)
    price = fields.Float(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


TransportScheduleCreate = TransportScheduleCreateSchema()
TransportScheduleUpdate = TransportScheduleUpdateSchema()
TransportScheduleResponse = TransportScheduleResponseSchema()

