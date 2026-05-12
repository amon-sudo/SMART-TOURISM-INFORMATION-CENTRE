import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Create the app instance
app = create_app()

if  __name__== "__main__":
    with app.app_context():
        from app.extensions import db
        db.create_all()
        print("Database tables created/verified.")
    app.run(debug=True)
