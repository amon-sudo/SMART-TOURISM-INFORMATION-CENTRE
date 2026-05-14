# app/feedback_media/schemas.py
from app.extensions import ma
from marshmallow import fields, validate, validates_schema, ValidationError
from .models import Review, MediaGallery, EmergencyContact

class ReviewSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Review
        load_instance = True
        include_fk = True
        ordered = True

    id = fields.UUID(dump_only=True)
    tourist_id = fields.UUID(required=True)
    target_type = fields.Str(required=True, validate=validate.Length(min=1, max=64))
    target_id = fields.UUID(required=True)
    rating = fields.Int(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.Str(allow_none=True, validate=validate.Length(max=500))
    status = fields.Str(allow_none=True, validate=validate.Length(max=32))
    created_at = fields.DateTime(dump_only=True)


class MediaGallerySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = MediaGallery
        load_instance = True
        ordered = True

    id = fields.UUID(dump_only=True)
    target_type = fields.Str(required=True, validate=validate.Length(min=1, max=64))
    target_id = fields.UUID(required=True)
    url = fields.Url(required=True, relative=False)
    media_type = fields.Str(allow_none=True, validate=validate.Length(max=64))
    is_primary = fields.Bool(load_default=False)
    created_at = fields.DateTime(dump_only=True)


class EmergencyContactSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = EmergencyContact
        load_instance = True
        include_fk = True
        ordered = True

    id = fields.UUID(dump_only=True)
    destination_id = fields.UUID(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    type = fields.Str(allow_none=True, validate=validate.Length(max=64))
    phone = fields.Str(allow_none=True, validate=validate.Length(max=64))
    street = fields.Str(allow_none=True, validate=validate.Length(max=200))
    city = fields.Str(allow_none=True, validate=validate.Length(max=100))
    region = fields.Str(allow_none=True, validate=validate.Length(max=100))
    location = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)

    @validates_schema
    def validate_location(self, data, **kwargs):
        loc = data.get("location")
        if loc:
            # Accept "POINT(lon lat)" or "lon,lat"
            if loc.strip().upper().startswith("POINT("):
                return
            if "," in loc:
                parts = loc.split(",")
                if len(parts) == 2:
                    try:
                        float(parts[0].strip())
                        float(parts[1].strip())
                        return
                    except ValueError:
                        pass
            raise ValidationError("location must be WKT POINT(lon lat) or 'lon,lat'")
