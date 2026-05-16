# main.py
import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.utils.setup import verify_environment

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        if verify_environment():
            print("--- System Ready: Environment and Database Verified ---")
            app.run(debug=True)
        else:
            print("--- System Start Failed: Environment check failed. Check server logs. ---")
