import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from app import extensions
from app.routes.payment_routesmpesa import payment_mpesa_bp
from app.Business import register_business_blueprints
from app.Business.errors_handling import register_business_error_handlers
from app.rbac.controllers.routes.role_routes import role_bp
from app.rbac.controllers.routes.permission_routes import permission_bp
from app.user_settings import models

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/smart_tourism"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
    app.register_blueprint(role_bp)
    app.register_blueprint(permission_bp)

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

    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "version": "1.0.0", "message": "Smart Tourism API is running"}), 200

    return app
