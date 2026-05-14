# app/__init__.py

import os
from logging.config import dictConfig
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import text

from app.extensions import db, migrate, jwt, ma
from app.routes.payment_routesmpesa import payment_mpesa_bp
from app.routes.rbac import rbac_bp
from app.Business import register_business_blueprints
from app.Business.errors_handling import register_business_error_handlers
from app.rbac.controllers.routes.role_routes import role_bp
from app.rbac.controllers.routes.permission_routes import permission_bp
from app.tourism_amenitties import register_blueprints as register_tourism_blueprints
from app.user_settings.views.views import user_settings_bp
from app.utils.responses import ApiResponse

# Ensure models are registered with SQLAlchemy
from app.user_settings import models as user_settings_models  # noqa: F401
from app.tourism_amenitties import models as tourism_models   # noqa: F401

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv(
        "SQLALCHEMY_TRACK_MODIFICATIONS", "False"
    ).lower() in ("1", "true", "yes")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    PROPAGATE_EXCEPTIONS = True
    JSON_SORT_KEYS = False


def configure_logging():
    dictConfig({
        "version": 1,
        "formatters": {
            "default": {"format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"}
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default"
            }
        },
        "root": {"level": os.getenv("LOG_LEVEL", "INFO"), "handlers": ["wsgi"]}
    })


def register_blueprints(flask_app):
    """Register blueprints safely to avoid circular imports."""
    try:
        # Core modules
        flask_app.register_blueprint(payment_mpesa_bp, url_prefix="/api/payments")
        register_business_blueprints(flask_app)
        register_business_error_handlers(flask_app)
        register_tourism_blueprints(flask_app)
        flask_app.register_blueprint(user_settings_bp, url_prefix="/api/v1")
        flask_app.register_blueprint(rbac_bp)
        flask_app.register_blueprint(role_bp)
        flask_app.register_blueprint(permission_bp)

        # Feedback & Media
        from app.feedback_media import feedback_bp
        flask_app.register_blueprint(feedback_bp)

        flask_app.logger.info("Registered all blueprints successfully")
    except Exception as exc:
        flask_app.logger.exception("Failed to register blueprints: %s", exc)


def register_error_handlers(flask_app):
    from werkzeug.exceptions import HTTPException

    @flask_app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({"error": e.name, "message": e.description}), e.code

    @flask_app.errorhandler(404)
    def not_found(e):
        return ApiResponse.error(message="Resource not found", code="NOT_FOUND", status_code=404)

    @flask_app.errorhandler(500)
    def handle_500(e):
        flask_app.logger.exception("Unhandled exception")
        return jsonify({
            "error": "internal_server_error",
            "message": "An internal error occurred"
        }), 500


def create_app(config_class=Config):
    """Application factory. Returns a configured Flask app instance."""
    configure_logging()
    flask_app = Flask(__name__, instance_relative_config=False)
    flask_app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    jwt.init_app(flask_app)
    ma.init_app(flask_app)

    # Enable CORS
    CORS(flask_app, resources={r"/api/*": {"origins": "*"}})

    # Import models so Alembic sees them
    import app.feedback_media.models

    # Register blueprints and error handlers
    register_blueprints(flask_app)
    register_error_handlers(flask_app)

    @flask_app.route("/api/v1/health", methods=["GET"])
from dotenv import load_dotenv
from app.extensions import db, migrate, jwt, cache
from app.rbac.controllers.routes.role_routes import role_bp
from app.rbac.controllers.routes.permission_routes import permission_bp
from app.audit.controllers.routes.audit_log_routes import audit_bp
from app.tourism_amenitties.registry import  redis_configure, register_blueprints
from app.user_settings import models  # noqa: F401

load_dotenv()


def create_app():
    app = Flask(__name__)
    
    
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    os.getenv("DATABASE_URL", "sqlite:///test.db")
)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///test.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this-in-production")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    #  redis init
    redis_configure(app)
    cache.init_app(app)
    
    app.register_blueprint(role_bp)
    app.register_blueprint(permission_bp)
    app.register_blueprint(audit_bp)
    register_blueprints(app)
    
    
    @app.route("/api/v1/health", methods=["GET"])
     # Debugging line to check registered routes
    def health():
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "message": "Smart Tourism API is running"
        }), 200

    @flask_app.route("/db-test")
    def db_test():
        try:
            db.session.execute(text("SELECT 1"))
            return {"db": "connected"}
        except Exception as e:
            return {"db": "error", "message": str(e)}, 500

    @flask_app.cli.command("create-tables")
    def create_tables():
        """Create DB tables (development only). Prefer migrations for production."""
        with flask_app.app_context():
            import app.feedback_media.models  # ensure all models are loaded
            db.create_all()
            print("Database tables created/verified.")

    return flask_app
    return app
