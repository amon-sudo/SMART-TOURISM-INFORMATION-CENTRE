import uuid, datetime
from app.extensions import db
from app.authanduser.models.models import User, RefreshToken, PasswordReset
from app.authanduser.utils.utils import hash_password, verify_password
from flask_jwt_extended import create_access_token, create_refresh_token

class AuthService:
    @staticmethod
    def signup(email, password, username=None, full_name=None):
        if User.query.filter_by(email=email).first():
            return None

        # Deduplicate username — append incrementing suffix until unique.
        if username:
            base = username
            attempt = username
            counter = 2
            while User.query.filter_by(username=attempt).first():
                attempt = f"{base}{counter}"
                counter += 1
            username = attempt

        user = User(email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # populate user.id before creating profile

        if full_name:
            from app.user_settings.models.models import UserProfile
            db.session.add(UserProfile(user_id=user.id, full_name=full_name))

        db.session.commit()
        return user

    @staticmethod
    def login(email, password):
        user = User.query.filter_by(email=email).first()
        if user and verify_password(user.password_hash, password):
            additional_claims = {"is_admin": bool(getattr(user, "is_admin", False))}
            access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
            refresh_token = create_refresh_token(identity=str(user.id))
            try:
                rt = RefreshToken(
                    user_id=user.id,
                    token=refresh_token,
                    expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7)
                )
                db.session.add(rt)
                # STORY012: track last successful login on the user's profile.
                if getattr(user, "profile", None) is not None:
                    user.profile.last_login_at = datetime.datetime.utcnow()
                db.session.commit()
            except Exception:
                db.session.rollback()
            return {"access_token": access_token, "refresh_token": refresh_token, "user": user}
        return None

    @staticmethod
    def logout(refresh_token, user_id=None, revoke_all: bool = False):
        """Revoke the supplied refresh token. When revoke_all is True (or no
        token was supplied but a user_id is known), revoke every active
        refresh token for the user — used by password reset and by the
        'log out everywhere' flow.
        """
        try:
            if revoke_all and user_id is not None:
                RefreshToken.query.filter_by(user_id=user_id, revoked=False).update(
                    {"revoked": True}
                )
            elif refresh_token:
                rt = RefreshToken.query.filter_by(token=refresh_token).first()
                if rt:
                    rt.revoked = True
            db.session.commit()
        except Exception:
            db.session.rollback()
        return True

    @staticmethod
    def request_password_reset(email):
        user = User.query.filter_by(email=email).first()
        if not user:
            return None
        reset_token = str(uuid.uuid4())
        try:
            pr = PasswordReset(
                user_id=user.id,
                token=reset_token,
                expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            )
            db.session.add(pr)
            db.session.commit()
            return pr
        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def confirm_password_reset(token, new_password):
        pr = PasswordReset.query.filter_by(token=token).first()
        if not pr or pr.expires_at <= datetime.datetime.utcnow():
            return False
        if hasattr(pr, "used") and getattr(pr, "used"): return False
        if hasattr(pr, "used_at") and getattr(pr, "used_at") is not None: return False

        user = db.session.get(User, pr.user_id)
        if not user: return False

        user.password_hash = hash_password(new_password)
        if hasattr(pr, "used"): pr.used = True
        if hasattr(pr, "used_at"): pr.used_at = datetime.datetime.utcnow()

        # STORY014: revoke every active refresh token so any device that
        # was logged in with the old password is forced to re-authenticate.
        RefreshToken.query.filter_by(user_id=user.id, revoked=False).update(
            {"revoked": True}
        )

        db.session.commit()
        return True

    @staticmethod
    def get_user(user_id):
        try:
            return User.query.get(uuid.UUID(user_id))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def generate_access_token(user_id):
        return create_access_token(identity=str(user_id))

    @staticmethod
    def get_or_create_google_user(email):
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, password_hash=hash_password(str(uuid.uuid4())))
            db.session.add(user)
            db.session.commit()
        return user

    @staticmethod
    def generate_tokens(user_id):
        return {
            "access_token": create_access_token(identity=str(user_id)),
            "refresh_token": create_refresh_token(identity=str(user_id))
        }
