# main.py
import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Create the app instance
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
