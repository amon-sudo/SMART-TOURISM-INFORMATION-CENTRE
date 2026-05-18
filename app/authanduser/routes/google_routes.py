from flask import Blueprint, url_for, current_app
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
    try:
        # authorize_access_token() exchanges the code AND (when using a
        # server_metadata_url) auto-parses + validates the id_token. The
        # parsed claims are placed under token['userinfo'].
        token = oauth.google.authorize_access_token()
    except Exception as exc:
        current_app.logger.exception("Google OAuth callback failed")
        return ApiResponse.error(
            message="Google login failed",
            code="OAUTH_FAILED",
            status_code=400,
            details={"reason": str(exc)},
        )

    userinfo = (token or {}).get("userinfo") or {}
    # Fall back to the userinfo endpoint if for any reason the id_token
    # claims came back empty (older flows, missing openid scope, etc.).
    if not userinfo:
        try:
            userinfo = oauth.google.userinfo(token=token) or {}
        except Exception:
            userinfo = {}

    email = userinfo.get("email")
    if not email:
        return ApiResponse.error(
            message="Google did not return an email address",
            code="OAUTH_NO_EMAIL",
            status_code=400,
        )

    user = AuthService.get_or_create_google_user(email)
    # generate_tokens expects a stringified identity (JWT sub claim).
    tokens = AuthService.generate_tokens(str(user.id))
    return ApiResponse.success(
        data={
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": getattr(user, "username", None),
            },
        },
        message="Google login successful",
    )
