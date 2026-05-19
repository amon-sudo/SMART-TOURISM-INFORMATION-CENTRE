import json
from app import create_app

app = create_app()
client = app.test_client()
attraction_id = 'ea81becf-ab6d-4a95-9459-70df5a2d53b5'
response = client.get(f'/api/public/attractions/{attraction_id}/profile')
print(f'Status: {response.status_code}')
data = response.get_json()
print(f'Data: {json.dumps(data, indent=2)}')
keys = data.keys() if data else []
print(f"Contains county: {'county' in data if data else False}")
print(f"Contains locality: {'locality' in data if data else False}")
print(f"Contains infrastructure_status: {'infrastructure_status' in data if data else False}")
