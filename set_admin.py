from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.session.execute(db.text("UPDATE users SET is_admin = true WHERE email = 'admin@example.com'"))
    db.session.commit()
    r = db.session.execute(db.text("SELECT email, is_admin FROM users WHERE is_admin = true"))
    print("Admin users:")
    for row in r:
        print(" ", row)
