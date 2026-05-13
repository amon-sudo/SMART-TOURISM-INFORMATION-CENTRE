from app import create_app

app = create_app()

if __name__ == "__main__":
    # Ensure tables exist (for dev/demo; migrations handle schema in production)
    with app.app_context():
        from app.extensions import db
        db.create_all()
        print("Database tables created/verified.")
    app.run(debug=True)
