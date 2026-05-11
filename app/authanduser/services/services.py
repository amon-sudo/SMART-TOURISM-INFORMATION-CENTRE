import uuid, datetime
from app.authanduser.extensions import db
from app.authanduser.models.models import User, RefreshToken, PasswordReset
from app.authanduser.utils.utils import hash_password, verify_password, generate_jwt

class AuthService:
    @staticmethod
    def signup(email, password):
        if User.query.filter_by(email=email).first():
            return None
        user = User(email=email, password_hash=hash_password(password))
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def login(email, password):
        user = User.query.filter_by(email=email).first()
        if user and verify_password(user.password_hash, password):
            access_token = generate_jwt(user.id)
            refresh_token = str(uuid.uuid4())
            rt = RefreshToken(
                user_id=user.id,
                token=refresh_token,
                expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7)
            )
            db.session.add(rt)
            db.session.commit()
            return {"access_token": access_token, "refresh_token": refresh_token, "user": user}
        return None

    @staticmethod
    def logout(refresh_token):
        rt = RefreshToken.query.filter_by(token=refresh_token).first()
        if rt:
            rt.revoked = True
            db.session.commit()
        return True

    @staticmethod
    def request_password_reset(email):
        user = User.query.filter_by(email=email).first()
        if not user:
            return None
        reset_token = str(uuid.uuid4())
        pr = PasswordReset(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        )
        db.session.add(pr)
        db.session.commit()
        return pr

    @staticmethod
    def confirm_password_reset(token, new_password):
        pr = PasswordReset.query.filter_by(token=token, used=False).first()
        if pr and pr.expires_at > datetime.datetime.utcnow():
            user = User.query.get(pr.user_id)
            user.password_hash = hash_password(new_password)
            pr.used = True
            db.session.commit()
            return True
        return False
