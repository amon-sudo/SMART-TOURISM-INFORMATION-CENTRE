"""
Auth package initializer.

Call init_auth_blueprint(app) from your application factory after db.init_app(app).
"""
from typing import Any

def init_auth_blueprint(app: Any) -> None:
    # import routes here to avoid top-level import side effects
    from .routes import auth_bp
    app.register_blueprint(auth_bp)
