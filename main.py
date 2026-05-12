from app import create_app
from dotenv import load_dotenv
load_dotenv()

app = create_app()

if  __name__== "__main__":
    with app.app_context():
        from app.extensions import db
        db.create_all()
        print("Database tables created/verified.")
    app.run(debug=True)