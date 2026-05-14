# main.py
import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Keep your group’s initialization so nothing is lost
    with app.app_context():
        from app.extensions import db
        db.create_all()

    # Run the app (from feature branch)
    app.run(debug=True)
