import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from app.extensions import db, migrate, jwt
from app.transport_feature import create_transport_feature_blueprint

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this-in-production")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    transport_feature_bp = create_transport_feature_blueprint()
    app.register_blueprint(transport_feature_bp)

    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200

    return app