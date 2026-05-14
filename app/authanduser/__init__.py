# app/authanduser/__init__.py
from flask import Flask, jsonify
from app.authanduser.extensions import db, migrate, jwt
from app.authanduser.config import Config   # import Config from here

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # load DB URI, secret keys, etc.

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # health route
    @app.route('/api/v1/health', methods=["GET"])
    def start():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200

    # register auth blueprint under /api/v1/auth
    from app.authanduser.routes.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")

    return app
