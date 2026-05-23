from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    tables = ['users','destinations','attractions','accommodations','room_types','events','tour_packages','bookings']
    for t in tables:
        r = db.session.execute(db.text(f'SELECT COUNT(*) FROM {t}'))
        print(t, r.scalar())
    r = db.session.execute(db.text("SELECT name, status, latitude, longitude FROM attractions WHERE status='approved' LIMIT 5"))
    print('Approved attractions with coords:')
    for row in r:
        print(' ', row)
