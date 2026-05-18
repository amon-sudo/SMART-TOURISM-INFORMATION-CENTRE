import os
from urllib.parse import urlencode, urlparse, urlunparse

from flask import Blueprint, url_for, current_app, redirect, request
from app.utils.oauth import oauth
from app.authanduser.services.services import AuthService
from app.utils.responses import ApiResponse

google_auth_bp = Blueprint("google_auth_bp", __name__)


def _frontend_callback_url(success: bool) -> str | None:
    """Resolve the frontend page the OAuth callback should redirect to.

    Returns None when no FRONTEND_OAUTH_REDIRECT_URL env var is set, in
    which case the callback falls back to a JSON response (useful for
    backend smoke testing without a frontend).
    """
    base = os.getenv("FRONTEND_OAUTH_REDIRECT_URL")
    if not base:
        return None
    # Optional override per-request via ?return_to=<absolute-or-path>
    # — handy when the same callback route lands users on different
    # frontend pages (profile, dashboard, last-visited route, etc.).
    override = request.args.get("return_to") or request.args.get("state")
    if override and override.startswith(("http://", "https://", "/")):
        return override
    if not success:
        # Append /error so the frontend can show a friendly error page
        # instead of silently dumping the user on /profile.
        parsed = urlparse(base)
        path = parsed.path.rstrip("/") + "/error"
        return urlunparse(parsed._replace(path=path))
    return base


@google_auth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for("google_auth_bp.google_authorize", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@google_auth_bp.route("/oauth/debug")
def oauth_debug():
    """Diagnostic — shows what the live process sees, so you can tell
    whether a stale .env or unrestarted server is the problem."""
    from flask import jsonify
    return jsonify({
        "FRONTEND_OAUTH_REDIRECT_URL_env": os.getenv("FRONTEND_OAUTH_REDIRECT_URL"),
        "resolved_success_redirect": _frontend_callback_url(success=True),
        "resolved_failure_redirect": _frontend_callback_url(success=False),
        "google_callback_url": url_for("google_auth_bp.google_authorize", _external=True),
    })


@google_auth_bp.route("/authorize/google")
def google_authorize():
    try:
        # authorize_access_token() exchanges the code AND (when using a
        # server_metadata_url) auto-parses + validates the id_token. The
        # parsed claims are placed under token['userinfo'].
        token = oauth.google.authorize_access_token()
    except Exception as exc:
        current_app.logger.exception("Google OAuth callback failed")
        fallback = _frontend_callback_url(success=False)
        if fallback:
            qs = urlencode({"error": "oauth_failed", "reason": str(exc)[:120]})
            sep = "&" if "?" in fallback else "?"
            return redirect(f"{fallback}{sep}{qs}")
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
        fallback = _frontend_callback_url(success=False)
        if fallback:
            qs = urlencode({"error": "no_email"})
            sep = "&" if "?" in fallback else "?"
            return redirect(f"{fallback}{sep}{qs}")
        return ApiResponse.error(
            message="Google did not return an email address",
            code="OAUTH_NO_EMAIL",
            status_code=400,
        )

    user = AuthService.get_or_create_google_user(email)
    # generate_tokens expects a stringified identity (JWT sub claim).
    tokens = AuthService.generate_tokens(str(user.id))

    # Hand the tokens off to the frontend (preferred) or fall back to JSON.
    redirect_base = _frontend_callback_url(success=True)
    if redirect_base:
        # Tokens go in the URL *fragment* (#...) so they never appear in
        # server access logs or HTTP Referer headers — the frontend JS
        # reads window.location.hash, parses it, then immediately calls
        # history.replaceState() to strip the fragment from the address bar.
        fragment = urlencode({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "user_id": str(user.id),
            "email": user.email,
        })
        return redirect(f"{redirect_base}#{fragment}")

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
