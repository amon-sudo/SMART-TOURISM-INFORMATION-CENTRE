import os
from flask import Flask, jsonify
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from app.extensions import db, migrate, jwt
# from app.routes.rbac import rbac_bp

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this-in-production")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.user_settings.views.views import user_settings_bp
# app.register_blueprint(rbac_bp)
    app.register_blueprint(user_settings_bp, url_prefix='/api/v1')

    @app.route("/api/v1/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200

    return app