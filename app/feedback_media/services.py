from app.extensions import db
from sqlalchemy.exc import IntegrityError
from .models import Review, MediaGallery, EmergencyContact, GEOGRAPHY_AVAILABLE

# Geo libs are optional — only imported when PostGIS is enabled
try:
    from geoalchemy2.shape import from_shape  # type: ignore
    from shapely.geometry import Point  # type: ignore
except Exception:  # pragma: no cover - dev fallback when PostGIS is off
    from_shape = None
    Point = None


def _as_dict(payload):
    if isinstance(payload, dict):
        return payload
    try:
        return payload.__dict__
    except Exception:
        raise TypeError("Payload must be a dictionary-like object")

def create_review(payload: dict) -> Review:
    payload = _as_dict(payload)
    review = Review(
        tourist_id=payload["tourist_id"],
        target_type=payload["target_type"],
        target_id=payload["target_id"],
        rating=payload["rating"],
        comment=payload.get("comment"),
        status=payload.get("status", "pending"),
    )
    db.session.add(review)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise
    return review

def add_media(payload: dict) -> MediaGallery:
    payload = _as_dict(payload)
    target_type = payload["target_type"]
    target_id = payload["target_id"]
    is_primary = bool(payload.get("is_primary", False))

    try:
        # transaction: if new media is primary, unset existing primary for same target
        with db.session.begin_nested():
            if is_primary:
                db.session.query(MediaGallery).filter(
                    MediaGallery.target_type == target_type,
                    MediaGallery.target_id == target_id,
                    MediaGallery.is_primary == True
                ).update({"is_primary": False}, synchronize_session=False)

            media = MediaGallery(
                target_type=target_type,
                target_id=target_id,
                url=payload["url"],
                media_type=payload.get("media_type"),
                is_primary=is_primary
            )
            db.session.add(media)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise
    return media

def add_contact(payload: dict) -> EmergencyContact:
    payload = _as_dict(payload)
    # Accept location as "POINT(lon lat)" or "lon,lat"
    loc = payload.get("location")
    geo = None
    if loc:
        loc = loc.strip()
        if loc.upper().startswith("POINT("):
            # assume valid WKT
            geo = loc
        else:
            # parse "lon,lat"
            lon_str, lat_str = [p.strip() for p in loc.split(",")]
            lon = float(lon_str)
            lat = float(lat_str)
            if GEOGRAPHY_AVAILABLE and Point is not None and from_shape is not None:
                try:
                    geo = from_shape(Point(lon, lat), srid=4326)
                except Exception:
                    geo = f"POINT({lon} {lat})"
            else:
                # SQLite/non-PostGIS dev mode — store as WKT text
                geo = f"POINT({lon} {lat})"

    contact = EmergencyContact(
        destination_id=payload["destination_id"],
        name=payload["name"],
        type=payload.get("type"),
        phone=payload.get("phone"),
        street=payload.get("street"),
        city=payload.get("city"),
        region=payload.get("region"),
        location=geo
    )
    db.session.add(contact)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise
    return contact

# Query helpers
def list_reviews(filters: dict, page: int = 1, per_page: int = 20):
    q = db.session.query(Review)
    if filters.get("target_type"):
        q = q.filter(Review.target_type == filters["target_type"])
    if filters.get("target_id"):
        q = q.filter(Review.target_id == filters["target_id"])
    if filters.get("tourist_id"):
        q = q.filter(Review.tourist_id == filters["tourist_id"])
    if filters.get("status"):
        q = q.filter(Review.status == filters["status"])
    q = q.order_by(Review.created_at.desc())
    items = q.limit(per_page).offset((page - 1) * per_page).all()
    return items

def list_media(target_type=None, target_id=None):
    q = db.session.query(MediaGallery)
    if target_type:
        q = q.filter(MediaGallery.target_type == target_type)
    if target_id:
        q = q.filter(MediaGallery.target_id == target_id)
    q = q.order_by(MediaGallery.is_primary.desc())
    return q.all()

def list_contacts(destination_id=None):
    q = db.session.query(EmergencyContact)
    if destination_id:
        q = q.filter(EmergencyContact.destination_id == destination_id)
    return q.all()

def delete_contact(contact_id) -> bool:
    contact = db.session.query(EmergencyContact).filter_by(id=contact_id).first()
    if not contact:
        return False
    db.session.delete(contact)
    db.session.commit()
    return True
