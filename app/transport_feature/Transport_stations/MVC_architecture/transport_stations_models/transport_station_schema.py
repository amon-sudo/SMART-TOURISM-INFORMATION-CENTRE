from marshmallow import Schema, fields, validate


STATION_TYPE_VALUES = ["bus_terminal", "train_station", "airport", "shuttle_terminal"]


class StationLocationSchema(Schema):
    latitude = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180, max=180))


class TransportStationSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(max=100))
    type = fields.String(required=True, validate=validate.OneOf(STATION_TYPE_VALUES))
    street = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    city = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    region = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    location = fields.Nested(StationLocationSchema, required=False, allow_none=True)
    country = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))


class TransportStationCreateSchema(TransportStationSchema):
    pass


class TransportStationUpdateSchema(Schema):
    name = fields.String(required=False, validate=validate.Length(max=100))
    type = fields.String(required=False, validate=validate.OneOf(STATION_TYPE_VALUES))
    street = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    city = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    region = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    location = fields.Nested(StationLocationSchema, required=False, allow_none=True)
    country = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))


class TransportStationResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.String(dump_only=True)
    type = fields.String(dump_only=True)
    street = fields.String(dump_only=True)
    city = fields.String(dump_only=True)
    region = fields.String(dump_only=True)
    country = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


TransportStationCreate = TransportStationCreateSchema()
TransportStationUpdate = TransportStationUpdateSchema()
TransportStationResponse = TransportStationResponseSchema()

