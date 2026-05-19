from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()
cache = Cache()

# Default rate-limit ceiling protects every endpoint; stricter per-route
# limits attached via @limiter.limit("...") in the auth and password-reset
# routes. Storage URI is configurable via RATELIMIT_STORAGE_URI (Redis in
# production, in-memory for dev).
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120 per minute"],
    headers_enabled=True,
)
