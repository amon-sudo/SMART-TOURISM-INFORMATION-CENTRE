# This file is intentionally left mostly empty to prevent blueprint nesting.
# The blueprints are registered directly in app/__init__.py.
def redis_configure(app):
    # Use a local-safe default cache backend for development and smoke tests.
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300
