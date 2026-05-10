from flask import Flask, jsonify
from dotenv import load_dotenv
from .extensions import db, migrate, ma
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/smart_tourism')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # Import and register blueprints
    from .user_settings.views.views import user_settings_bp
    app.register_blueprint(user_settings_bp, url_prefix='/api/v1/user')

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"message": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"message": "An internal server error occurred"}), 500

    @app.route('/api/v1/health', methods=["GET"])
    def start():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200
    
    return app