from app import create_app
from app.extensions import db
from app.tourism_amenitties.attractions.models.attraction import Attraction
from sqlalchemy import func

app = create_app()
with app.app_context():
    def get_counts(categories, status='approved'):
        count = db.session.query(Attraction).filter(
            Attraction.status == status,
            Attraction.category.in_(categories)
        ).count()
        return count

    print("--- 1) lowercase ---")
    c1 = get_counts(['wildlife', 'adventure'])
    print(f"status='approved', categories=['wildlife', 'adventure']: {c1}")

    print("\n--- 2) PascalCase ---")
    c2 = get_counts(['Wildlife', 'Adventure'])
    print(f"status='approved', categories=['Wildlife', 'Adventure']: {c2}")

    print("\n--- 3) Grouped by status and category ---")
    results = db.session.query(
        Attraction.status,
        Attraction.category,
        func.count(Attraction.id)
    ).group_by(Attraction.status, Attraction.category).all()
    
    for s, c, count in results:
        print(f"Status: {s}, Category: {c}, Count: {count}")
