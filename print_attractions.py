from app import create_app
from app.extensions import db
from app.tourism_amenitties.attractions.models.attraction import Attraction

app = create_app()

target_names = [
    "Nairobi National Park",
    "Fort Jesus",
    "Maasai Mara National Reserve",
    "Hell's Gate National Park",
    "Lake Naivasha Boat Safari"
]

with app.app_context():
    print("--- Requested Attractions ---")
    attractions = Attraction.query.filter(Attraction.name.in_(target_names)).all()
    for name in target_names:
        found = False
        for attr in attractions:
            if attr.name == name:
                print(f"Name: {attr.name}")
                print(f"Image URL: {attr.image_url}")
                print("-" * 20)
                found = True
                break
        if not found:
            print(f"Name: {name} (Not found in DB)")
            print("-" * 20)

    print("\n--- Statistics ---")
    total_with_images = Attraction.query.filter(Attraction.image_url.isnot(None)).count()
    print(f"Total attractions with non-null image_url: {total_with_images}")
