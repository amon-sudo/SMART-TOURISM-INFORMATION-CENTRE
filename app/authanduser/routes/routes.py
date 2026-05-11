from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.authanduser.services.services import AuthService
from app.authanduser.schemas import UserSchema, PasswordResetSchema

# Blueprint without prefix (prefix is set in app/__init__.py)
auth_bp = Blueprint("auth", __name__)

user_schema = UserSchema()
password_reset_schema = PasswordResetSchema()

# Signup
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    user = AuthService.signup(data.get("email"), data.get("password"))
    if not user:
        return jsonify({"error": "Email already exists"}), 400
    return jsonify(user_schema.dump(user)), 201

# Login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    tokens = AuthService.login(data.get("email"), data.get("password"))
    if not tokens:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "user": user_schema.dump(tokens["user"])
    }), 200

# Me
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    current_user_id = get_jwt_identity()   # identity is UUID string
    user = AuthService.get_user(current_user_id)  # cast back to UUID inside service
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_schema.dump(user)), 200

# Logout
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    data = request.get_json() or {}
    AuthService.logout(data.get("refresh_token"))
    return jsonify({"message": "Logged out"}), 200

# Password reset request
@auth_bp.route("/password-reset", methods=["POST"])
def password_reset():
    data = request.get_json() or {}
    pr = AuthService.request_password_reset(data.get("email"))
    if not pr:
        return jsonify({"error": "User not found"}), 404
    return jsonify(password_reset_schema.dump(pr)), 200

# Password reset confirm
@auth_bp.route("/password-reset/confirm", methods=["POST"])
def password_reset_confirm():
    data = request.get_json() or {}
    success = AuthService.confirm_password_reset(
        data.get("reset_token"),
        data.get("new_password")
    )
    if not success:
        return jsonify({"error": "Invalid or expired token"}), 400
    return jsonify({"message": "Password updated"}), 200

# Refresh token
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()   # identity is UUID string
    new_access_token = AuthService.generate_access_token(current_user_id)
    return jsonify({"access_token": new_access_token}), 200
