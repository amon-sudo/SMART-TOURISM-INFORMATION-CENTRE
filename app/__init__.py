import os
from flask import Flask, jsonify
from extensions import db, migrate
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("POSTGRES_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    from app.tourismAmenitties.amenities.models import amenities
    from app.tourismAmenitties.attractions.models import attraction
    from app.tourismAmenitties.destination.models import destination
    from app.tourismAmenitties.attraction_translations.models import attraction_tran
    from app.tourismAmenitties.destination_translation.models import destinationTranslation
    from app.tourismAmenitties.attraction_amenities.models import attractionAmmenities

    @app.route("/db-test")
    def db_test():
        db.session.execute(text("SELECT 1"))
        return {"db": "connected"}

    @app.route("/api/v1/health")
    def start():
        return {"status": "ok", "version": "1.0.0"}, 200

    return app