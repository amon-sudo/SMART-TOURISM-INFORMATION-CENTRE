from datetime import datetime
from ...models.user_domain.user_domain import User
from ...models.user_repo.user_repository import UserRepository
from ...models.user_schema.user_schema import UserSchema
from app.models.user_role import UserRole



class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.user_schema = UserSchema()

    def register_user(self, user_data):
        return self.user_repo.register_user(user_data)

    def login_user(self, username, password):
        return self.user_repo.login_user(username, password)

    def logout_user(self, user_id):
        return self.user_repo.logout_user(user_id)

    def get_user_by_id(self, user_id):
        return self.user_repo.get_user_by_id(user_id)
    
    def get_user_by_username(self, username):
        return self.user_repo.get_user_by_username(username)
    
    def get_user_by_email(self, email):
        return self.user_repo.get_user_by_email(email)
    
    def get_user_roles(self, user_id):
        return self.user_repo.get_user_roles(user_id)

    def get_all_users(self):
        return self.user_repo.get_all_users()

    def update_user(self, user_id, update_data):
        return self.user_repo.update_user(user_id, update_data)

    def delete_user(self, user_id):
        return self.user_repo.delete_user(user_id)      