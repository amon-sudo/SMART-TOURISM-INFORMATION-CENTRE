# This file is intentionally left mostly empty to prevent blueprint nesting.
# The blueprints are registered directly in app/__init__.py.
import os

def redis_configure(app):
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        app.config["CACHE_TYPE"] = "RedisCache"
        app.config["CACHE_REDIS_URL"] = redis_url
    else:
        # No Redis configured — disable caching so DB changes (e.g. attraction
        # approvals) are always visible immediately without a cache bust delay.
        app.config["CACHE_TYPE"] = "NullCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300
