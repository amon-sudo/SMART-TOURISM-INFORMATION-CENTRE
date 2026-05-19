import sys
import traceback
from uuid import UUID
from app import create_app
from app.itinerary_feature.MVC_architecture.services.itinerary_generator_service import ItineraryGeneratorService

def validate():
    app = create_app()
    with app.app_context():
        try:
            service = ItineraryGeneratorService()
            user_id = UUID('00000000-0000-0000-0000-000000000001')
            itinerary = service.generate(
                user_id=user_id,
                duration_days=2,
                interests=['wildlife', 'adventure'],
                budget_level='medium',
                pace='moderate',
                accessibility_required=False,
                destination='Nairobi',
                language='en'
            )
            
            print(f"SUCCESS")
            print(f"ID: {itinerary.id}")
            print(f"Title: {itinerary.title}")
            print(f"Days: {len(itinerary.days)}")
            for day in itinerary.days:
                print(f"Day {day.day_number}: {len(day.attractions)} stops")
                
        except Exception as e:
            print("FAILURE")
            traceback.print_exc()

if __name__ == "__main__":
    validate()
