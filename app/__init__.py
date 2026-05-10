import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from app.extensions import db, migrate, jwt
from app.routes.rbac import rbac_bp
from app.authanduser import init_auth_blueprint   # <-- your addition

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this-in-production")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(rbac_bp)
    init_auth_blueprint(app)   # <-- register your auth endpoints

    # Health check route
    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200

    return app
