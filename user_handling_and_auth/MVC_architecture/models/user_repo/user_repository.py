from app.extensions import db
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError


from user_handling_and_auth.MVC_architecture.models.user_domain.user_domain import User
from user_handling_and_auth.MVC_architecture.models.user_schema.user_schema import UserSchema
from app.models.user_role import UserRole


class UserRepository:
    def __init__(self):
        self.model = User
        self.schema = UserSchema()

    def register_user(self, user_data):
        try:
            data = self.schema.load(user_data)
            user = User(
                username=data["username"],
                email=data["email"],
                is_active=data.get("is_active", True),
            )
            user.set_password(data["password"])
            db.session.add(user)
            db.session.commit()
            return user
        except ValidationError as ve:
            db.session.rollback()
            raise ve
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae
        
    def login_user(self, username, password):
        user = self.model.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None

    def logout_user(self, user_id):
        return True

    def get_user_by_id(self, user_id):
        user = self.model.query.get(user_id)
        if user is None:
            return None
        return user

    def get_all_users(self):
        return self.model.query.all()

    def update_user(self, user_id, update_data):
        user = self.model.query.get(user_id)
        if user is None:
            return None
        try:
            for key, value in update_data.items():
                if key == "password":
                    user.set_password(value)
                elif hasattr(user, key):
                    setattr(user, key, value)
            db.session.commit()
            return user
        except ValidationError as ve:
            db.session.rollback()
            raise ve
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae

    def delete_user(self, user_id):
        user = self.model.query.get(user_id)
        if user is None:
            return False
        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae
    
    def get_user_by_username(self, username):
        user = self.model.query.filter_by(username=username).first()
        if user is None:
            return None
        return user

    def get_user_by_email(self, email):
        user = self.model.query.filter_by(email=email).first()
        if user is None:
            return None
        return user

    def get_user_roles(self, user_id):
        return UserRole.query.filter_by(user_id=user_id).all()
    
    def restore_deleted_user(self, user_id):
        user = self.model.query.get(user_id)
        if user is None or user.deleted_at is None:
            return None
        try:
            user.deleted_at = None
            db.session.commit()
            return user
        except SQLAlchemyError as sae:
            db.session.rollback()
            raise sae