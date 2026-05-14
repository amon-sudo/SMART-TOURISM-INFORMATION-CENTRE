# app/__init__.py
import os
from logging.config import dictConfig
from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_cors import CORS

from app.extensions import db, migrate, jwt, ma

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
        from app.feedback_media import feedback_bp
        flask_app.register_blueprint(feedback_bp)
        flask_app.logger.info("Registered feedback_media blueprint")
    except Exception as exc:
        flask_app.logger.exception("Failed to register feedback_media blueprint: %s", exc)


def register_error_handlers(flask_app):
    from werkzeug.exceptions import HTTPException

    @flask_app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({"error": e.name, "message": e.description}), e.code

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
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200

    @flask_app.cli.command("create-tables")
    def create_tables():
        """Create DB tables (development only). Prefer migrations for production."""
        with flask_app.app_context():
            import app.feedback_media.models  # ensure all models are loaded
            db.create_all()
            print("Database tables created/verified.")

    return flask_app
