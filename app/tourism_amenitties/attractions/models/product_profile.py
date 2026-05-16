from app.extensions import db
from app.utils.base_model import BaseUUIDModel

class TourismProductProfile(BaseUUIDModel):
    __tablename__ = "tourism_product_profiles"

    attraction_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("attractions.id"), nullable=False, unique=True)
    
    # 2. Location
    county = db.Column(db.String(100))
    sub_county = db.Column(db.String(100))
    ward = db.Column(db.String(100))
    locality = db.Column(db.String(255))
    gps_coordinates = db.Column(db.String(100))
    
    # 3. Features
    unique_features = db.Column(db.Text)
    conservation_efforts = db.Column(db.Text)
    visitor_capacity = db.Column(db.Integer)
    experience_types = db.Column(db.String(255)) # e.g. "guided,self-guided"
    average_stay_time = db.Column(db.String(100))
    best_visiting_period = db.Column(db.String(100))
    key_events = db.Column(db.Text)
    
    # 4. Situational Analysis
    infrastructure_status = db.Column(db.JSON) # Roads, Kiosks, Fencing, Water, Signage, Parking, Toilets
    site_status = db.Column(db.String(50)) # e.g. "active", "under development"
    
    # 5. Stakeholders
    tour_operators = db.Column(db.Text)
    nearby_accommodation = db.Column(db.Text)
    local_guides = db.Column(db.Text)
    distance_to_hub = db.Column(db.String(100))
    
    # 6. Community
    community_role = db.Column(db.Text)
    community_benefits = db.Column(db.Text)
    community_enterprises = db.Column(db.Text)
    
    # 7. Recommendations
    competitiveness_assessment = db.Column(db.Text)
    infrastructure_gaps = db.Column(db.Text)
    sustainability_strategies = db.Column(db.Text)
    growth_opportunities = db.Column(db.Text)
    community_empowerment = db.Column(db.Text)
    other_observations = db.Column(db.Text)

    attraction = db.relationship("Attraction", backref=db.backref("profile", uselist=False))
