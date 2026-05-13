from app import create_app
from app.extensions import db
from app.user_settings.models.models import User

app = create_app()

def seed_data():
    with app.app_context():
        # Check if test user exists by email (since IDs are now UUIDs)
        user = User.query.filter_by(email="test@example.com").first()
        if not user:
            print("Creating test user...")
            new_user = User(email="test@example.com")
            db.session.add(new_user)
            db.session.commit()
            print(f"Test user created successfully with ID: {new_user.id}")
        else:
            print(f"Test user already exists with ID: {user.id}")

if __name__ == "__main__":
    seed_data()
