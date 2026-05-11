
from ..Business_profile_schema.Business_profile_schema import BusinessProfileSchema
from ..Business_profile_domain.Business_profile_domain import BusinessProfile
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from marshmallow import ValidationError

class BusinessProfileRepository:

    def create_business_profile(self, business_data):
        try:
            data = BusinessProfileSchema().load(business_data)
            business_profile = BusinessProfile(**data)
            db.session.add(business_profile)
            db.session.commit()
            return business_profile
        except ValidationError as ve:
            db.session.rollback()
            raise ve
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae
        
    def get_business_profile_by_id(self, business_id):
        business_profile = BusinessProfile.query.get(business_id)
        if business_profile is None:
            return None
        return business_profile
    
    def get_all_business_profiles(self):
        return BusinessProfile.query.all()
    
#businesses to submit their business profile for approval by admin, admin can approve or reject the business profile, if approved the business profile will be visible to users, if rejected the business profile will be deleted from the database.
    def update_business_profile(self, business_id, update_data):
        business_profile = BusinessProfile.query.get(business_id)
        if business_profile is None:
            return None
        try:
            for key, value in update_data.items():
                setattr(business_profile, key, value)
            db.session.commit()
            return business_profile
        except ValidationError as ve:
            db.session.rollback()
            raise ve
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae

    def delete_business_profile(self, business_id):
        business_profile = BusinessProfile.query.get(business_id)
        if business_profile is None:
            return False
        try:
            db.session.delete(business_profile)
            db.session.commit()
            return True
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae



    