import json
from main import app

def test_generate_itinerary():
    with app.test_client() as client:
        payload = {
            "duration_days": 2,
            "interests": ["wildlife", "adventure"],
            "budget_level": "medium",
            "pace": "moderate",
            "accessibility_required": False,
            "destination": "Nairobi",
            "language": "en"
        }
        response = client.post(
            "/api/v1/itineraries/generate",
            data=json.dumps(payload),
            content_type='application/json'
        )
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:")
            print(json.dumps(response.get_json(), indent=2))
        except Exception as e:
            print("Failed to parse JSON response:")
            print(response.data.decode('utf-8'))

if __name__ == "__main__":
    test_generate_itinerary()
