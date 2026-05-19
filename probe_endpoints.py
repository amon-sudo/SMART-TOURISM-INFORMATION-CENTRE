from app import create_app
import json

app = create_app()
client = app.test_client()

endpoints = [
    "/api/v1/health",
    "/api/v1/transport/routes/routes/",
    "/api/v1/transport/routes/routes/active",
    "/api/v1/transport/schedules/schedules/",
    "/api/v1/transport/stations/stations/",
    "/api/v1/destinations/",
    "/api/v1/attractions/?include_all=true",
    "/api/v1/events",
    "/api/public/welcome"
]

for ep in endpoints:
    response = client.get(ep)
    try:
        data = response.get_json()
        msg = ''
        if isinstance(data, dict):
            msg = data.get('message') or data.get('error') or data.get('status') or list(data.keys())[0]
        elif isinstance(data, list):
            msg = f'List of {len(data)} items'
    except:
        msg = response.data.decode('utf-8')[:50]
    print(f'{ep} => {response.status_code} {msg}')
