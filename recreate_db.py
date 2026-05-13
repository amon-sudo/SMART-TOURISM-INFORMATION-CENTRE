from app import create_app
from app.extensions import db
from app.user_settings.models.models import User

app = create_app()

def recreate_and_seed():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        
        print("Seeding test user...")
        # UUID is generated automatically
        new_user = User(email="test@example.com")
        db.session.add(new_user)
        db.session.commit()
        print(f"Database recreated and seeded successfully. Created user with ID: {new_user.id}")

if __name__ == "__main__":
    recreate_and_seed()
