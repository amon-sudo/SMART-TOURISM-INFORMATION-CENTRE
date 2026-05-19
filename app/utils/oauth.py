from authlib.integrations.flask_client import OAuth
from flask import current_app, url_for, redirect, session

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)
    # Use Google's OpenID discovery document so authlib can auto-populate
    # authorization_endpoint / token_endpoint / userinfo_endpoint / jwks_uri.
    # Without server_metadata_url, parse_id_token() crashes with
    # 'Missing "jwks_uri" in metadata' because there's nothing to fetch
    # Google's signing keys from.
    oauth.register(
        name='google',
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )
