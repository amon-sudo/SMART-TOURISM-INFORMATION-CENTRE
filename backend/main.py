from flask import Flask, jsonify
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
@app.route('/API/v1/Health', methods=["GET"])
def start():
    return jsonify( {"status": "ok", "version": "1.0.0"})
if  __name__== "__main__":
    app.run(debug=True)