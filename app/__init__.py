from __future__ import annotations

import os
from logging.config import dictConfig

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text

from app.Business import register_business_blueprints
from app.audit.controllers.routes.audit_log_routes import audit_bp
from app.extensions import cache, db, jwt, ma, migrate
from app.feedback_media import feedback_bp
from app.payment_stripe.controllers.controllers import payment_stripe_bp
from app.rbac.controllers.routes.permission_routes import permission_bp
from app.rbac.controllers.routes.role_routes import role_bp
from app.routes.payment_routesmpesa import payment_mpesa_bp
from app.tourism_amenitties import register_blueprints as register_tourism_blueprints
from app.tourism_amenitties import redis_configure
from app.user_settings.views.views import user_settings_bp

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///dev.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    PROPAGATE_EXCEPTIONS = True
    JSON_SORT_KEYS = False


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                }
            },
            "root": {"level": os.getenv("LOG_LEVEL", "INFO"), "handlers": ["wsgi"]},
        }
    )


def register_blueprints(flask_app: Flask) -> None:
    """Register all application blueprints."""
    try:
        flask_app.register_blueprint(payment_mpesa_bp, url_prefix="/api/payments")
        flask_app.register_blueprint(payment_stripe_bp, url_prefix="/api/v1/payments/stripe")
        register_business_blueprints(flask_app)
        register_tourism_blueprints(flask_app)
        flask_app.register_blueprint(user_settings_bp, url_prefix="/api/v1")
        flask_app.register_blueprint(role_bp)
        flask_app.register_blueprint(permission_bp)
        flask_app.register_blueprint(audit_bp)
        flask_app.register_blueprint(feedback_bp)
        flask_app.logger.info("Registered all blueprints successfully")
    except Exception as exc:
        flask_app.logger.exception("Failed to register blueprints: %s", exc)


def register_error_handlers(flask_app: Flask) -> None:
    from werkzeug.exceptions import HTTPException

    @flask_app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({"error": error.name, "message": error.description}), error.code

    @flask_app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "not_found", "message": "Resource not found"}), 404

    @flask_app.errorhandler(500)
    def handle_500(error):
        flask_app.logger.exception("Unhandled exception")
        return jsonify(
            {"error": "internal_server_error", "message": "An internal error occurred"}
        ), 500


def create_app(config_class=Config):
    """Application factory. Returns a configured Flask app instance."""
    configure_logging()

    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    redis_configure(app)
    cache.init_app(app)

    # Import representative models so migrations and metadata see them.
    from app.feedback_media import models as feedback_media_models  # noqa: F401
    from app.tourism_amenitties import models as tourism_models  # noqa: F401
    from app.user_settings import models as user_settings_models  # noqa: F401

    with app.app_context():
        # Ensure missing tables exist in local development DBs.
        db.create_all()

        # Lightweight sqlite compatibility for historical schema drift.
        if db.engine.dialect.name == "sqlite":
            conn = db.session.connection()

            def has_column(table_name: str, column_name: str) -> bool:
                rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                return any(row[1] == column_name for row in rows)

            def column_type(table_name: str, column_name: str) -> str | None:
                rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                for row in rows:
                    if row[1] == column_name:
                        return str(row[2]).upper()
                return None

            # Migrate legacy integer users.id to UUID-text style for current models.
            if column_type("users", "id") == "INTEGER":
                conn.execute(text("PRAGMA foreign_keys=OFF"))
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS users_new (
                            id VARCHAR(36) PRIMARY KEY,
                            email VARCHAR(255) NOT NULL UNIQUE,
                            password_hash VARCHAR(255),
                            created_at DATETIME,
                            updated_at DATETIME
                        )
                        """
                    )
                )
                conn.execute(
                    text(
                        """
                        INSERT INTO users_new (id, email, password_hash, created_at, updated_at)
                        SELECT lower(hex(randomblob(16))), email, password_hash, created_at, updated_at
                        FROM users
                        """
                    )
                )
                conn.execute(text("DROP TABLE users"))
                conn.execute(text("ALTER TABLE users_new RENAME TO users"))
                conn.execute(text("PRAGMA foreign_keys=ON"))

            if has_column("users", "id") and not has_column("users", "password_hash"):
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))

            if has_column("users", "id") and not has_column("users", "updated_at"):
                conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))

            if has_column("destinations", "id") and not has_column("destinations", "canonical_name"):
                conn.execute(text("ALTER TABLE destinations ADD COLUMN canonical_name VARCHAR"))

            if has_column("destinations", "id") and not has_column("destinations", "slug"):
                conn.execute(text("ALTER TABLE destinations ADD COLUMN slug VARCHAR"))

            if has_column("destinations", "id") and not has_column("destinations", "updated_at"):
                conn.execute(text("ALTER TABLE destinations ADD COLUMN updated_at DATETIME"))

            db.session.commit()

    register_blueprints(app)
    register_error_handlers(app)

    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "message": "Smart Tourism API is running"}), 200

    @app.route("/db-test")
    def db_test():
        try:
            from sqlalchemy import text

            db.session.execute(text("SELECT 1"))
            return jsonify({"db": "connected"})
        except Exception as exc:
            return jsonify({"db": "error", "message": str(exc)}), 500

    return app
