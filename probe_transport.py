from app import create_app
import json

app = create_app()
client = app.test_client()

endpoints = [
    '/api/v1/transport/routes/',
    '/api/v1/transport/routes/active',
    '/api/v1/transport/schedules/',
    '/api/v1/transport/stations/',
    '/api/v1/transport/stations/search?city=Nairobi',
    '/api/v1/transport/stations/nearby?latitude=-1.286389&longitude=36.817223&radius_km=5'
]

for ep in endpoints:
    response = client.get(ep)
    try:
        data = response.get_json()
        if isinstance(data, dict):
            summary = str(data)[:100] + '...' if len(str(data)) > 100 else str(data)
        elif isinstance(data, list):
            summary = f'List of {len(data)} items'
        else:
            summary = str(data)[:100]
    except:
        summary = response.data.decode('utf-8')[:100]
    print(f'{ep} => {response.status_code} {summary}')
