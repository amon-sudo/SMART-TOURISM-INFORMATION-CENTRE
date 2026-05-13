import os
from flask import Flask
from dotenv import load_dotenv
from app import extensions
from app.routes.payment_routesmpesa import payment_mpesa_bp

def create_app():
    load_dotenv()
    app = Flask(__name__)

    # Config: PostgreSQL connection
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/smart_tourism"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Fail fast if JWT secret is missing
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY must be set in environment")
    app.config["JWT_SECRET_KEY"] = jwt_secret

    # Initialize extensions
    extensions.db.init_app(app)
    extensions.migrate.init_app(app, extensions.db)
    extensions.jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(payment_mpesa_bp, url_prefix="/api/payments")

    return app
