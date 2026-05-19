import json
from app import create_app

app = create_app()
client = app.test_client()

def test_probe():
    # 1) GET /api/v1/attractions/?include_all=true
    resp1 = client.get('/api/v1/attractions/?include_all=true')
    print(f'1) GET /api/v1/attractions/?include_all=true: Status {resp1.status_code}')
    if resp1.status_code == 200:
        data = resp1.get_json()
        items = data.get('data', []) if isinstance(data, dict) else data
        if isinstance(items, list) and len(items) > 0:
            first_item = items[0]
            image_url = first_item.get('image_url')
            has_image = bool(image_url and image_url.strip())
            print(f'   First item image_url exists and non-empty: {has_image} (Value: {image_url})')
        else:
            print(f'   Items not found as list or empty. Keys: {data.keys() if isinstance(data, dict) else "N/A"}')
    
    # 2) GET /api/v1/transport/routes/ count
    resp2 = client.get('/api/v1/transport/routes/')
    print(f'2) GET /api/v1/transport/routes/: Status {resp2.status_code}')
    if resp2.status_code == 200:
        data = resp2.get_json()
        items = data.get('data', data) if isinstance(data, dict) else data
        print(f'   Count: {len(items) if isinstance(items, list) else "N/A"}')

    # 3) GET /api/v1/transport/schedules/ count
    resp3 = client.get('/api/v1/transport/schedules/')
    print(f'3) GET /api/v1/transport/schedules/: Status {resp3.status_code}')
    if resp3.status_code == 200:
        data = resp3.get_json()
        items = data.get('data', data) if isinstance(data, dict) else data
        print(f'   Count: {len(items) if isinstance(items, list) else "N/A"}')

    # 4) GET /api/v1/transport/stations/ count
    resp4 = client.get('/api/v1/transport/stations/')
    print(f'4) GET /api/v1/transport/stations/: Status {resp4.status_code}')
    if resp4.status_code == 200:
        data = resp4.get_json()
        items = data.get('data', data) if isinstance(data, dict) else data
        print(f'   Count: {len(items) if isinstance(items, list) else "N/A"}')

if __name__ == '__main__':
    test_probe()
