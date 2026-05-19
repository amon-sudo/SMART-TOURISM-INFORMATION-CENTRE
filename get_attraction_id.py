from app import create_app
from app.models import Attraction
app = create_app()
with app.app_context():
    attraction = Attraction.query.filter_by(name='Nairobi National Park').first()
    if attraction:
        print(attraction.id)
    else:
        print('Not found')
