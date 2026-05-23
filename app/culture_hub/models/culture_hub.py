import uuid
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID


class CultureHub(db.Model):
    __tablename__ = "culture_hubs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = db.Column(db.String(255), nullable=False)
    county = db.Column(db.String(100), nullable=False)
    sub_county = db.Column(db.String(100), nullable=True)
    ward = db.Column(db.String(100), nullable=True)
    locality = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Tourism product info
    tourism_type = db.Column(db.String(100), nullable=True)

    # Community involvement (section 6 of tourism products profile)
    community_role = db.Column(db.Text, nullable=True)
    community_benefits = db.Column(db.Text, nullable=True)
    community_enterprises = db.Column(db.JSON, nullable=True)  # [{type, name, description}]

    # Cultural activities (categorized by county)
    activities = db.Column(db.JSON, nullable=True)  # [{name, type, description, seasonal}]

    # Experience details
    unique_features = db.Column(db.Text, nullable=True)
    environmental_impact = db.Column(db.Text, nullable=True)
    visitor_capacity = db.Column(db.Integer, nullable=True)
    best_visiting_periods = db.Column(db.String(255), nullable=True)
    key_events = db.Column(db.Text, nullable=True)

    # Media
    image_url = db.Column(db.String(500), nullable=True)
    media_urls = db.Column(db.JSON, nullable=True)

    status = db.Column(db.String(50), default="active", nullable=False)

    contact_info = db.Column(db.JSON, nullable=True)  # {phone, email, website}

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "county": self.county,
            "sub_county": self.sub_county,
            "ward": self.ward,
            "locality": self.locality,
            "description": self.description,
            "tourism_type": self.tourism_type,
            "community_role": self.community_role,
            "community_benefits": self.community_benefits,
            "community_enterprises": self.community_enterprises or [],
            "activities": self.activities or [],
            "unique_features": self.unique_features,
            "environmental_impact": self.environmental_impact,
            "visitor_capacity": self.visitor_capacity,
            "best_visiting_periods": self.best_visiting_periods,
            "key_events": self.key_events,
            "image_url": self.image_url,
            "media_urls": self.media_urls or [],
            "status": self.status,
            "contact_info": self.contact_info or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
