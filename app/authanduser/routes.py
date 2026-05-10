from flask import Blueprint, request, jsonify
from app.authanduser.models import db, User, RefreshToken, PasswordReset
from app.authanduser.utils import hash_password, verify_password, generate_jwt, decode_jwt
from app.authanduser.schemas import UserSchema, RefreshTokenSchema, PasswordResetSchema
import uuid
import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

user_schema = UserSchema()
refresh_schema = RefreshTokenSchema()
password_reset_schema = PasswordResetSchema()

# POST /auth/signup
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    if User.query.filter_by(email=data.get("email")).first():
        return jsonify({"error": "Email already exists"}), 400
    user = User(
        email=data["email"],
        password_hash=hash_password(data["password"])
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user_schema.dump(user)), 201

# POST /auth/login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get("email")).first()
    if user and verify_password(user.password_hash, data.get("password")):
        access_token = generate_jwt(user.id)
        refresh_token = str(uuid.uuid4())
        rt = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7)
        )
        db.session.add(rt)
        db.session.commit()
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_schema.dump(user)
        }), 200
    return jsonify({"error": "Invalid credentials"}), 401

# POST /auth/refresh
@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json() or {}
    rt = RefreshToken.query.filter_by(token=data.get("refresh_token"), revoked=False).first()
    if not rt or rt.expires_at < datetime.datetime.utcnow():
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    new_access_token = generate_jwt(rt.user_id)
    return jsonify({"access_token": new_access_token}), 200

# POST /auth/logout
@auth_bp.route("/logout", methods=["POST"])
def logout():
    data = request.get_json() or {}
    rt = RefreshToken.query.filter_by(token=data.get("refresh_token")).first()
    if rt:
        rt.revoked = True
        db.session.commit()
    return jsonify({"message": "Logged out"}), 200

# GET /auth/me
@auth_bp.route("/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401
    token = auth_header.split(" ")[1]
    payload = decode_jwt(token)
    user = User.query.get(payload["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_schema.dump(user)), 200

# POST /auth/password-reset
@auth_bp.route("/password-reset", methods=["POST"])
def password_reset():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get("email")).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    reset_token = str(uuid.uuid4())
    pr = PasswordReset(
        user_id=user.id,
        token=reset_token,
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    )
    db.session.add(pr)
    db.session.commit()
    return jsonify(password_reset_schema.dump(pr)), 200

# POST /auth/password-reset/confirm
@auth_bp.route("/password-reset/confirm", methods=["POST"])
def password_reset_confirm():
    data = request.get_json() or {}
    pr = PasswordReset.query.filter_by(token=data.get("reset_token"), used=False).first()
    if pr and pr.expires_at > datetime.datetime.utcnow():
        user = User.query.get(pr.user_id)
        user.password_hash = hash_password(data["new_password"])
        pr.used = True
        db.session.commit()
        return jsonify({"message": "Password updated"}), 200
    return jsonify({"error": "Invalid or expired token"}), 400
