
import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from app.extensions import db, migrate, jwt
from app.rbac.controllers.routes.role_routes import role_bp
from app.rbac.controllers.routes.permission_routes import permission_bp
from app.audit.controllers.routes.audit_log_routes import audit_bp
from app.tourism_amenitties import  redis_configure
from app.user_settings import models  # noqa: F401

load_dotenv()


def create_app():
    app = Flask(__name__)
    
    
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "POSTGRES_URI",
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

    app.register_blueprint(role_bp)
    app.register_blueprint(permission_bp)
    app.register_blueprint(audit_bp)
    @app.route("/api/v1/health", methods=["GET"])
     # Debugging line to check registered routes
    def health():
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "message": "Smart Tourism API is running"
        }), 200

    return app
