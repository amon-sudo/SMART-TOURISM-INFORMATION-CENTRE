import os
from flask import Flask
from dotenv import load_dotenv
from app import extensions
from app.routes.payment_routesmpesa import payment_mpesa_bp

from flask import Flask, jsonify
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from sqlalchemy import text

from app.extensions import db, migrate, jwt
from app.routes.rbac import rbac_bp

# Load environment variables
load_dotenv()

def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY",
        "change-this-in-production"
    )

    # Init extensions
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

    return app
