import os
from flask import Flask
from dotenv import load_dotenv
from app.utils import extensions
from app.routes.payment_routesmpesa import payment_mpesa_bp

def create_app():
    load_dotenv()
    app = Flask(__name__)

    # Config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "supersecret")

    # Initialize extensions
    extensions.db.init_app(app)
    extensions.migrate.init_app(app, extensions.db)
    extensions.jwt.init_app(app)

    # Register blueprints (only here)
    app.register_blueprint(payment_mpesa_bp, url_prefix="/api/payments")

    return app

