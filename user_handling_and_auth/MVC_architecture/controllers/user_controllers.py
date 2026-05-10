
from user_handling_and_auth.MVC_architecture.Views.User_service.user_service import UserService
from ..models.user_schema.user_schema import UserSchema
from ..user_validators.user_validators import (
    validate_user_registration,
    validate_user_login,
    validate_user_update,
    validate_user_retrieval,
    validate_user_deletion,
)

class UserController:

    def __init__(self):
        self.user_service = UserService()
        self.user_schema = UserSchema()
        
    def register_user(self, user_data):
        valid, msg = validate_user_registration(user_data)
        if not valid:
            return {"error": msg}, 400
        try:
            user = self.user_service.register_user(user_data)
            return self.user_schema.dump(user), 201
        except Exception as e:
            return {"error": str(e)}, 500

    def login_user(self, username, password):
        valid, msg = validate_user_login({"username": username, "password": password})
        if not valid:
            return {"error": msg}, 400
        user = self.user_service.login_user(username, password)
        if user is None:
            return {"error": "Invalid credentials"}, 401
        return self.user_schema.dump(user), 200

    def get_user_by_id(self, user_id):
        valid, msg = validate_user_retrieval({"user_id": user_id})
        if not valid:
            return {"error": msg}, 400
        user = self.user_service.get_user_by_id(user_id)
        if user is None:
            return {"error": "User not found"}, 404
        return self.user_schema.dump(user), 200
    
    def get_all_users(self):
        users = self.user_service.get_all_users()
        return self.user_schema.dump(users, many=True), 200
    
    def update_user(self, user_id, update_data):
        valid, msg = validate_user_update(update_data)
        if not valid:
            return {"error": msg}, 400
        try:
            user = self.user_service.update_user(user_id, update_data)
            if user is None:
                return {"error": "User not found"}, 404
            return self.user_schema.dump(user), 200
        except Exception as e:
            return {"error": str(e)}, 500
        
    def delete_user(self, user_id):
        valid, msg = validate_user_deletion({"user_id": user_id})
        if not valid:
            return {"error": msg}, 400
        try:
            result = self.user_service.delete_user(user_id)
            if result is False:
                return {"error": "User not found"}, 404
            return {"message": "User deleted successfully"}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    