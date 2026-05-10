from flask import Flask, jsonify
from app.extensions import db
from app.authanduser import init_auth_blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")  # make sure Config has your DB URI etc.

    # initialize extensions
    db.init_app(app)

    # health route
    @app.route('/api/v1/health', methods=["GET"])
    def start():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200

    # register your auth blueprint
    init_auth_blueprint(app)

    return app
