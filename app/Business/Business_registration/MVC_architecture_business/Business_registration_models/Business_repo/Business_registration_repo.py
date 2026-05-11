from ..Business_schema.Business_registration_schema import BusinessRegistrationRequestCreateSchema
from ..Business_registration_domain.Business_registration_domain import BusinessRegistrationRequest
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from marshmallow import ValidationError

class BusinessRegistrationRepository:

    def create_registration_request(self, registration_data):
        try:
            data = BusinessRegistrationRequestCreateSchema().load(registration_data)
            registration_request = BusinessRegistrationRequest(**data)
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
        registration_request = BusinessRegistrationRequest.query.get(request_id)
        if registration_request is None:
            return None
        return registration_request

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
            raise sae
        