from marshmallow import Schema, fields

class StripePaymentIntentSchema(Schema):
    amount = fields.Int(required=True)  # Amount in cents
    currency = fields.Str(load_default="usd")
    metadata = fields.Dict(required=False)

class StripePaymentResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    stripe_payment_intent_id = fields.Str(dump_only=True)
    amount = fields.Decimal(dump_only=True)
    currency = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
