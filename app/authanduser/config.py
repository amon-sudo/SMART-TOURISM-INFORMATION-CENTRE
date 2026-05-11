import os

class Config:
    # Database connection
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://alvin_ndichu:alvin2003ndichu@localhost:5432/smart_tourism_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask secret key (used for sessions, CSRF, etc.)
    # Must be long and random for security
    SECRET_KEY = os.getenv("SECRET_KEY", "this_is_a_super_long_flask_secret_key_1234567890")

    # JWT secret key (used by flask-jwt-extended)
    # Must be at least 32 characters long for HMAC SHA256
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "this_is_a_very_long_jwt_secret_key_1234567890")

    # Optional: enable debug mode in development
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1", "yes"]
