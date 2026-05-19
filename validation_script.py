import sys
import json
import traceback
from main import app

def validate():
    client = app.test_client()
    payload = {
        "duration_days": 2,
        "interests": ["wildlife", "adventure"],
        "budget_level": "medium",
        "pace": "moderate",
        "accessibility_required": False,
        "destination": "Nairobi",
        "language": "en"
    }
    try:
        response = client.post('/api/v1/itineraries/generate', 
                               data=json.dumps(payload),
                               content_type='application/json')
        print(f"Status Code: {response.status_code}")
        try:
            print(json.dumps(response.get_json(), indent=2))
        except Exception:
            print(response.data.decode('utf-8'))
    except Exception:
        print("An error occurred during the request:")
        traceback.print_exc()

if __name__ == "__main__":
    validate()
