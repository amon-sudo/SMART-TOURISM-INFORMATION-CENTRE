import os

class Config:
    # Database connection
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://alvin_ndichu:alvin2003ndichu@localhost:5432/smart_tourism_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask secret key (used for sessions, CSRF, etc.)
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

    # JWT secret key (used by flask-jwt-extended)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-string")

    # Optional: enable debug mode in development
    DEBUG = True
