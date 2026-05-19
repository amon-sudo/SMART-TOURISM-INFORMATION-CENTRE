from __future__ import annotations

import uuid
from http import HTTPStatus
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from ..Business_profile_models.Business_profile_schema.Business_profile_schema import BusinessProfileSchema
from ..Business_profile_views.Business_profile_service.Business_profile_service import BusinessProfileService



_profile_update_schema = BusinessProfileUpdateSchema()
_profile_response_schema = BusinessProfileResponseSchema()
_profile_admin_response_schema = BusinessProfileAdminResponseSchema()

class BusinessProfileController:
    
    # @jwt_required()  # TEMP: auth disabled for endpoint testing
    def create_business_profile(self):
        user_id = get_jwt_identity()
        try:
            data = _profile_update_schema.load(request.json)
            profile = BusinessProfileService.create_business_profile(user_id, data)
            return _profile_response_schema.dump(profile), HTTPStatus.CREATED
        except ValidationError as ve:
            return {"error": ve.messages}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR  
        

    def get_business_profile(self, business_id):
        try:
            profile = BusinessProfileService.get_business_profile(business_id)
            if profile is None:
                return {"error": "Business profile not found"}, HTTPStatus.NOT_FOUND
            return _profile_response_schema.dump(profile), HTTPStatus.OK
        except Exception as e:
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
        

    def get_all_business_profiles(self):
        try:
            profiles = BusinessProfileService.get_all_business_profiles()
            return _profile_response_schema.dump(profiles, many=True), HTTPStatus.OK
        except Exception as e:
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
        
    def update_business_profile(self, business_id):
        user_id = get_jwt_identity()
        try:
            data = _profile_update_schema.load(request.json)
            profile = BusinessProfileService.update_business_profile(user_id, business_id, data)
            if profile is None:
                return {"error": "Business profile not found"}, HTTPStatus.NOT_FOUND
            return _profile_response_schema.dump(profile), HTTPStatus.OK
        except ValidationError as ve:
            return {"error": ve.messages}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
        
    def delete_business_profile(self, business_id):
        user_id = get_jwt_identity()
        try:
            result = BusinessProfileService.delete_business_profile(user_id, business_id)
            if not result:
                return {"error": "Business profile not found"}, HTTPStatus.NOT_FOUND
            return {"message": "Business profile deleted successfully"}, HTTPStatus.OK
        except Exception as e:
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR

    def approve_business_profile(self, business_id):
        user_id = get_jwt_identity()
        try:
            result = BusinessProfileService.approve_business_profile(user_id, business_id)
            if not result:
                return {"error": "Business profile not found or already approved"}, HTTPStatus.NOT_FOUND
            return {"message": "Business profile approved successfully"}, HTTPStatus.OK
        except Exception as e:
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
        
    def reject_business_profile(self, business_id):
        user_id = get_jwt_identity()
        try:
            result = BusinessProfileService.reject_business_profile(user_id, business_id)
            if not result:
                return {"error": "Business profile not found or already rejected"}, HTTPStatus.NOT_FOUND
            return {"message": "Business profile rejected successfully"}, HTTPStatus.OK
        except Exception as e:
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR