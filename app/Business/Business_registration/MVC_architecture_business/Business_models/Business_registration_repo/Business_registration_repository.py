from ..Business_domain.Business_registration_request_domain.Business_registration_request_domain import BusinessRegistrationRequest
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError



#handling CRUD operations for business registration requests, including submission, retrieval, updating, and deletion of registration requests. It also includes methods for approving or rejecting registration requests, as well as filtering requests based on various criteria such as status, business name, email, user ID, date range, and business type.

class BusinessRegistrationRepository:
    
    def submit_registration_request(self, registration_data):
        try:
            registration_request = BusinessRegistrationRequest(**registration_data)
            db.session.add(registration_request)
            db.session.commit()
            return registration_request
        except ValidationError as ve:
            db.session.rollback()
            raise ve
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae
        
    def get_registration_request_by_id(self, request_id):
        return BusinessRegistrationRequest.query.get(request_id)
    
    def get_all_registration_requests(self):
        return BusinessRegistrationRequest.query.all()
    
    def update_registration_request(self, request_id, update_data):
        registration_request = BusinessRegistrationRequest.query.get(request_id)
        if registration_request is None:
            return None
        try:
            for key, value in update_data.items():
                setattr(registration_request, key, value)
            db.session.commit()
            return registration_request
        except ValidationError as ve:
            db.session.rollback()
            raise ve
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae

    def delete_registration_request(self, request_id):
        registration_request = BusinessRegistrationRequest.query.get(request_id)
        if registration_request is None:
            return False
        try:
            db.session.delete(registration_request)
            db.session.commit()
            return True
        except SQLAlchemyError as sae:
            db.session.rollback()

    def approve_registration_request(self, request_id):
        registration_request = BusinessRegistrationRequest.query.get(request_id)
        if registration_request is None:
            return False
        try:
            registration_request.status = "approved"
            db.session.commit()
            return True
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae
        
    def reject_registration_request(self, request_id):
        registration_request = BusinessRegistrationRequest.query.get(request_id)
        if registration_request is None:
            return False
        try:
            db.session.delete(registration_request)
            db.session.commit()
            return True
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae
        
    def get_registration_requests_by_status(self, status):
        return BusinessRegistrationRequest.query.filter_by(status=status).all()
    
    def get_registration_requests_by_business_name(self, business_name):
        return BusinessRegistrationRequest.query.filter_by(business_name=business_name).all()
    
    def get_registration_requests_by_email(self, email):
        return BusinessRegistrationRequest.query.filter_by(email=email).all()   
    
    def get_registration_requests_by_user_id(self, user_id):
        return BusinessRegistrationRequest.query.filter_by(user_id=user_id).all()   

    def get_registration_requests_by_date_range(self, start_date, end_date):
        return BusinessRegistrationRequest.query.filter(
            BusinessRegistrationRequest.created_at >= start_date,
            BusinessRegistrationRequest.created_at <= end_date
        ).all()
    
    def get_registration_requests_by_business_type(self, business_type):
        return BusinessRegistrationRequest.query.filter_by(business_type=business_type).all()   


    #resubmitting the registration request after rejection, the business can update the registration details and resubmit the request for approval. The repository will handle the logic for updating the existing registration request with the new details and changing the status back to "pending" for re-evaluation by the admin.
    def resubmit_registration_request(self, request_id, update_data):
        registration_request = BusinessRegistrationRequest.query.get(request_id)
        if registration_request is None:
            return None
        try:
            for key, value in update_data.items():
                setattr(registration_request, key, value)
            registration_request.status = "pending"
            db.session.commit()
            return registration_request
        except ValidationError as ve:
            db.session.rollback()
            raise ve
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae
    
    def upload_supporting_documents(self, request_id, documents):
        registration_request = BusinessRegistrationRequest.query.get(request_id)
        if registration_request is None:
            return None
        try:
            registration_request.supporting_documents = documents
            db.session.commit()
            return registration_request
        except ValidationError as ve:
            db.session.rollback()
            raise ve
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae
    
