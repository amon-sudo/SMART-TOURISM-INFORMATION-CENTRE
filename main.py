import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from app import create_app, extensions

load_dotenv()

app = create_app()
migrate = Migrate(app, extensions.db)

if __name__ == "__main__":
    app.run(debug=True)
