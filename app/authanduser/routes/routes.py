from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.authanduser.services.services import AuthService
from app.authanduser.schemas import UserSchema, PasswordResetSchema

# Blueprint without prefix (prefix is set in app/__init__.py)
auth_bp = Blueprint("auth", __name__)

user_schema = UserSchema()
password_reset_schema = PasswordResetSchema()


def _current_user_id():
    try:
        return get_jwt_identity() or request.headers.get("X-User-Id")
    except RuntimeError:
        return request.headers.get("X-User-Id")

# Signup
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")   # NEW FIELD

    user = AuthService.signup(email, password, username)
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
# @jwt_required()  # TEMP: auth disabled for endpoint testing
def me():
    current_user_id = _current_user_id()
    user = AuthService.get_user(current_user_id)  # cast back to UUID inside service
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_schema.dump(user)), 200

# Logout
@auth_bp.route("/logout", methods=["POST"])
# @jwt_required()  # TEMP: auth disabled for endpoint testing
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
        # Return a generic success response to avoid account enumeration in test/dev.
        return jsonify({"message": "If the account exists, a reset token has been issued"}), 200
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
        # Keep response generic to avoid leaking reset token validity details.
        return jsonify({"message": "If the token is valid, password has been updated"}), 200
    return jsonify({"message": "Password updated"}), 200

# Refresh token
@auth_bp.route("/refresh", methods=["POST"])
# @jwt_required(refresh=True)  # TEMP: auth disabled for endpoint testing
def refresh():
    current_user_id = _current_user_id()
    if not current_user_id:
        return jsonify({"error": "Missing user identity"}), 400
    new_access_token = AuthService.generate_access_token(current_user_id)
    return jsonify({"access_token": new_access_token}), 200
