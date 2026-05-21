# main.py
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.utils.setup import verify_environment

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        if verify_environment():
            print("--- System Ready: Environment and Database Verified ---")
            app.run(debug=True, host="0.0.0.0", port=5000)
        else:
            print("--- System Start Failed: Environment check failed. Check server logs. ---")
