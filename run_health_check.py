import json
from app import create_app, db
from app.models.attraction import Attraction

app = create_app()
client = app.test_client()

def test_attractions():
    response = client.get('/api/v1/attractions/?include_all=true')
    status = response.status_code
    data = response.get_json()
    items = data.get('attractions', []) if isinstance(data, dict) else []
    has_image = any(item.get('image_url') for item in items)
    print(f"GET /api/v1/attractions/?include_all=true: {'Pass' if status == 200 and has_image else 'Fail'} (Status: {status}, Has Image: {has_image})")

def test_routes():
    response = client.get('/api/v1/transport/routes/')
    status = response.status_code
    data = response.get_json()
    count = len(data) if isinstance(data, list) else 0
    print(f"GET /api/v1/transport/routes/: {'Pass' if status == 200 else 'Fail'} (Status: {status}, Count: {count})")

def test_schedules():
    response = client.get('/api/v1/transport/schedules/')
    status = response.status_code
    data = response.get_json()
    count = len(data) if isinstance(data, list) else 0
    print(f"GET /api/v1/transport/schedules/: {'Pass' if status == 200 else 'Fail'} (Status: {status}, Count: {count})")

def test_profile():
    with app.app_context():
        a = Attraction.query.filter(Attraction.name.ilike('%Nairobi National Park%')).first()
        if not a:
            print("GET /api/public/attractions/<id>/profile: Fail (Nairobi National Park not found)")
            return
        n_id = a.id
    response = client.get(f'/api/public/attractions/{n_id}/profile')
    print(f"GET /api/public/attractions/{n_id}/profile: {'Pass' if response.status_code == 200 else 'Fail'} (Status: {response.status_code})")

def test_itinerary():
    payload = {
        "days": 2,
        "preferences": ["wildlife", "adventure"]
    }
    response = client.post('/api/v1/itineraries/generate', 
                           data=json.dumps(payload), 
                           content_type='application/json')
    status = response.status_code
    data = response.get_json()
    has_days = 'itinerary' in data and len(data['itinerary']) > 0 if isinstance(data, dict) else False
    print(f"POST /api/v1/itineraries/generate: {'Pass' if status == 200 and has_days else 'Fail'} (Status: {status}, Has Days: {has_days})")

if __name__ == '__main__':
    test_attractions()
    test_routes()
    test_schedules()
    test_profile()
    test_itinerary()
