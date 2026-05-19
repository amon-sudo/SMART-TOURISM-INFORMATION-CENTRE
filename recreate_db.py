from app import create_app
from app.extensions import db
from sqlalchemy import text
from flask_migrate import stamp
app = create_app()

from app.user_settings.models.models import User

def recreate_and_seed():
    with app.app_context():
        print("Cleaning database...")
        # For Postgres, dropping schema public is the cleanest way to wipe everything.
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO group_user; GRANT ALL ON SCHEMA public TO postgres;"))
        db.session.commit()
        
        print("Creating all tables...")
        db.create_all()
        
        stamp()
        print("Database initialized and stamped.")
        
        print("Seeding test user...")
        # UUID is generated automatically
        new_user = User(email="test@example.com")
        new_user.set_password("password123")
        db.session.add(new_user)
        db.session.commit()
        print(f"Database recreated and seeded successfully. Created user with ID: {new_user.id}")

if __name__ == "__main__":
    recreate_and_seed()
