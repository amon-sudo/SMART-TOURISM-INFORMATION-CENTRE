from app.user_settings.models import models
import os
from flask import Flask, jsonify
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from app.extensions import db, migrate, jwt
# from app.routes.rbac import rbac_bp

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///test.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this-in-production")

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Blueprints
    from app.user_settings.views.views import user_settings_bp
    app.register_blueprint(user_settings_bp, url_prefix='/api/v1')

    # Global Error Handlers (Standardized Enveloping)
    from app.utils.responses import ApiResponse

    @app.errorhandler(404)
    def not_found(e):
        return ApiResponse.error(message="Resource not found", code="NOT_FOUND", status_code=404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return ApiResponse.error(message="Method not allowed", code="METHOD_NOT_ALLOWED", status_code=405)

    @app.errorhandler(500)
    def internal_error(e):
        return ApiResponse.error(message="An internal server error occurred", code="INTERNAL_ERROR", status_code=500)
    from app.user_settings.views.views import user_settings_bp
# app.register_blueprint(rbac_bp)
    app.register_blueprint(user_settings_bp, url_prefix='/api/v1')
    # Register blueprints
    app.register_blueprint(rbac_bp, url_prefix="/api/v1")

    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200

    return app
