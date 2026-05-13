from app.extensions import db

class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True)
    business_profile = db.relationship("BusinessProfile", back_populates="media", uselist=False)

class Attraction(db.Model):
    __tablename__ = 'attractions'
    id = db.Column(db.Uuid(as_uuid=True), primary_key=True)
    business_profile_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey('business_profiles.id'))
    business_profile = db.relationship("BusinessProfile", back_populates="attractions")
