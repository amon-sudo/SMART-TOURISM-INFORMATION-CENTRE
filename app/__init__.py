import os
from flask import Flask
from dotenv import load_dotenv
from app import extensions
from app.routes.payment_routesmpesa import payment_mpesa_bp

from flask import Flask, jsonify
from dotenv import load_dotenv
from sqlalchemy import text

from app.extensions import db, migrate, jwt

from app.Business import register_business_blueprints
from app.Business.errors_handling import register_business_error_handlers

from app.rbac.controllers.routes.role_routes import role_bp
from app.rbac.controllers.routes.permission_routes import permission_bp

from app.user_settings import models  # noqa: F401

load_dotenv()


def create_app():
    load_dotenv()
    app = Flask(__name__)
    
    
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("POSTGRES_URI")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "POSTGRES_URI",
        os.getenv("DATABASE_URL", "sqlite:///test.db")
    )

    # Config: PostgreSQL connection
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/smart_tourism"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Fail fast if JWT secret is missing
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY must be set in environment")
    app.config["JWT_SECRET_KEY"] = jwt_secret

    # Initialize extensions
    extensions.db.init_app(app)
    extensions.migrate.init_app(app, extensions.db)
    extensions.jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(payment_mpesa_bp, url_prefix="/api/payments")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///test.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY",
        "change-this-in-production"
    )

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    
    # REGISTER TOURISM MODULES
    
    from app.tourism_amenitties import models
    from app.tourism_amenitties import register_blueprints

    register_blueprints(app)

    
    # REGISTER BUSINESS MODULES
    
    register_business_blueprints(app)
    register_business_error_handlers(app)

    
    # USER SETTINGS
    
    from app.user_settings.views.views import user_settings_bp

    app.register_blueprint(
        user_settings_bp,
        url_prefix="/api/v1"
    )

    
    # RBAC
    
    app.register_blueprint(role_bp)
    app.register_blueprint(permission_bp)

    
    # TEST ROUTE
    
    @app.route("/db-test")
    def db_test():
        db.session.execute(text("SELECT 1"))
        return {"db": "connected"}

    
    # HEALTH ROUTE
    
    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "message": "Smart Tourism API is running"
        }), 200

    
    # ERROR HANDLERS
    
    from app.utils.responses import ApiResponse

    @app.errorhandler(404)
    def not_found(e):
        return ApiResponse.error(
            message="Resource not found",
            code="NOT_FOUND",
            status_code=404
        )

    @app.errorhandler(405)
    def method_not_allowed(e):
        return ApiResponse.error(
            message="Method not allowed",
            code="METHOD_NOT_ALLOWED",
            status_code=405
        )

    @app.errorhandler(500)
    def internal_error(e):
        return ApiResponse.error(
            message="An internal server error occurred",
            code="INTERNAL_ERROR",
            status_code=500
        )

    return app