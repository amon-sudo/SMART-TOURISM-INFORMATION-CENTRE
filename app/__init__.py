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
   

    from app.tourism_amenitties import models


    from app.tourism_amenitties import register_blueprints
    
    register_blueprints(app)

    @app.route("/db-test")
    def db_test():
        db.session.execute(text("SELECT 1"))
        return {"db": "connected"}

    @app.route("/api/v1/health")
    def start():
        return {"status": "ok", "version": "1.0.0"}, 200
    # print(app.url_map)
    return app