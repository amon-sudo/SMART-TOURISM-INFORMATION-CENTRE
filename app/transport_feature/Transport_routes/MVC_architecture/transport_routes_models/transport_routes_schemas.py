from marshmallow import Schema, fields, validate


ROUTE_TYPE_VALUES = ["bus", "train", "flight", "shuttle"]


class LocationCoordinates(Schema):
    latitude = fields.Float(
        required=True,
        validate=validate.Range(min=-90, max=90),
        metadata={"description": "Latitude must be between -90 and 90"},
    )
    longitude = fields.Float(
        required=True,
        validate=validate.Range(min=-180, max=180),
        metadata={"description": "Longitude must be between -180 and 180"},
    )


class TransportRouteSchema(Schema):
    origin_station_id = fields.UUID(required=True)
    destination_station_id = fields.UUID(required=False, allow_none=True)
    type = fields.String(required=True, validate=validate.OneOf(ROUTE_TYPE_VALUES))
    duration_minutes = fields.Integer(required=True, validate=validate.Range(min=1))
    base_fare = fields.Float(required=True, validate=validate.Range(min=0))
    is_active = fields.Boolean(load_default=True)


class TransportRouteCreateSchema(TransportRouteSchema):
    pass


class TransportRouteUpdateSchema(Schema):
    origin_station_id = fields.UUID(required=False)
    destination_station_id = fields.UUID(required=False, allow_none=True)
    type = fields.String(required=False, validate=validate.OneOf(ROUTE_TYPE_VALUES))
    duration_minutes = fields.Integer(required=False, validate=validate.Range(min=1))
    base_fare = fields.Float(required=False, validate=validate.Range(min=0))
    is_active = fields.Boolean(required=False)


class TransportRoutesResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    type = fields.String(dump_only=True)
    origin_station_id = fields.UUID(dump_only=True)
    duration_minutes = fields.Integer(dump_only=True)
    base_fare = fields.Float(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


TransportRouteCreate = TransportRouteCreateSchema()
TransportRouteUpdate = TransportRouteUpdateSchema()
TransportRoutesResponse = TransportRoutesResponseSchema()