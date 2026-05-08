

from flask import Flask, jsonify
from dotenv import load_dotenv
load_dotenv()
def create_app():
    app = Flask(__name__)
    @app.route('/api/v1/Health', methods=["GET"])
    def start():
     return jsonify( {"status": "ok", "version": "1.0.0"})
    return app