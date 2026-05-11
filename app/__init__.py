import os
from flask import Flask, jsonify

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

from app.extensions import db, migrate, jwt
from app.routes.rbac import rbac_bp
from app.user_handling_and_auth.MVC_architecture.controllers.user_routes import user_blueprint
from app.Business.Business_registration.MVC_architecture_business.Business_controllers.Business_registrationroutes import business_bp
from app.Business.Business_registration.MVC_architecture_business.Business_controllers.Business_registration_routes_admin import business_admin_bp

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this-in-production")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(rbac_bp)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(business_bp)
    app.register_blueprint(business_admin_bp)

    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200

    return app