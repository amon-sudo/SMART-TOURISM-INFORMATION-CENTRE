from flask import Blueprint, url_for, session, redirect, jsonify
from app.utils.oauth import oauth
from app.authanduser.services.services import AuthService
from app.utils.responses import ApiResponse

google_auth_bp = Blueprint("google_auth_bp", __name__)

@google_auth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for("google_auth_bp.google_authorize", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@google_auth_bp.route("/authorize/google")
def google_authorize():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token)
    
    # Logic to find or create user
    email = user_info.get("email")
    user = AuthService.get_or_create_google_user(email)
    
    # Generate JWT
    tokens = AuthService.generate_tokens(user.id)
    return ApiResponse.success(data=tokens, message="Google login successful")
