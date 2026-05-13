from app import create_app
from app.extensions import db
from app.user_settings.models.models import User

app = create_app()

def seed_data():
    with app.app_context():
        # Check if test user exists
        user = User.query.get(1)
        if not user:
            print("Creating test user with ID 1...")
            new_user = User(id=1, email="test@example.com")
            db.session.add(new_user)
            db.session.commit()
            print("Test user created successfully.")
        else:
            print("Test user already exists.")

if __name__ == "__main__":
    seed_data()
