import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from app import extensions
from app.routes.payment_routesmpesa import payment_mpesa_bp

from flask import Flask, jsonify
from dotenv import load_dotenv
from sqlalchemy import text

from app.extensions import db, migrate, jwt
from app.routes.rbac import rbac_bp
# Extension imports
from app.extensions import db, migrate, jwt

# Module-specific imports
from app.Business import register_business_blueprints
from app.Business.errors_handling import register_business_error_handlers
from app.rbac.controllers.routes.role_routes import role_bp
from app.rbac.controllers.routes.permission_routes import permission_bp
from app.user_settings import models
from app.routes.payment_routesmpesa import payment_mpesa_bp
from app.tourism_amenitties import register_blueprints as register_tourism_blueprints
from app.user_settings.views.views import user_settings_bp
from app.utils.responses import ApiResponse

# Ensure models are registered with SQLAlchemy
from app.user_settings import models as user_settings_models # noqa: F401
from app.tourism_amenitties import models as tourism_models # noqa: F401

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/smart_tourism"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY",
        "change-this-in-production"
    )
    
    # Database Configuration (Strict PostgreSQL)
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URI")
    if not database_url:
        raise ValueError("No DATABASE_URL or POSTGRES_URI set in environment")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Security Configuration
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY must be set in environment")
    app.config["JWT_SECRET_KEY"] = jwt_secret

    extensions.db.init_app(app)
    extensions.migrate.init_app(app, extensions.db)
    extensions.jwt.init_app(app)

    app.register_blueprint(payment_mpesa_bp, url_prefix="/api/payments")
    register_business_blueprints(app)
    register_business_error_handlers(app)

    from app.user_settings.views.views import user_settings_bp
    app.register_blueprint(user_settings_bp, url_prefix='/api/v1')
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(rbac_bp)

    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200
        return ApiResponse.error(
            message="An internal server error occurred",
            code="INTERNAL_ERROR",
            status_code=500
        )
    # Register Blueprints
    
    # 1. Payments
    app.register_blueprint(payment_mpesa_bp, url_prefix="/api/payments")
    
    # 2. Business
    register_business_blueprints(app)
    register_business_error_handlers(app)
    
    # 3. Tourism
    register_tourism_blueprints(app)
    
    # 4. User Settings
    app.register_blueprint(user_settings_bp, url_prefix="/api/v1")
    
    # 5. RBAC (Roles & Permissions)
    app.register_blueprint(role_bp)
    app.register_blueprint(permission_bp)

    # Core Utility Routes
    
    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "message": "Smart Tourism API is running"
        }), 200

    @app.route("/db-test")
    def db_test():
        try:
            db.session.execute(text("SELECT 1"))
            return {"db": "connected"}
        except Exception as e:
            return {"db": "error", "message": str(e)}, 500

    # Standardized Global Error Handlers
    
    @app.errorhandler(404)
    def not_found(e):
        return ApiResponse.error(message="Resource not found", code="NOT_FOUND", status_code=404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return ApiResponse.error(message="Method not allowed", code="METHOD_NOT_ALLOWED", status_code=405)

    @app.errorhandler(500)
    def internal_error(e):
        return ApiResponse.error(message="An internal server error occurred", code="INTERNAL_ERROR", status_code=500)

    return app