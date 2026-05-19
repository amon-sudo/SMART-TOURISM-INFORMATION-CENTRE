from app import create_app
import json
import os
app = create_app()
client = app.test_client()
def test_workflow():
    print("--- 1) POST /api/v1/itineraries ---")
    resp = client.post('/api/v1/itineraries', json={"title": "Frontend QR Create Test"})
    data = resp.get_json()
    itinerary_id = data.get('id') if data else None
    print(f"Status: {resp.status_code}")
    if data:
        print(f"Itinerary ID: {itinerary_id}")
        print(f"QR Code URL Presence: {'qr_code_url' in data}")
    if itinerary_id:
        print("\n--- 2) POST /api/v1/itineraries/%s/qr" % itinerary_id)
        resp = client.post('/api/v1/itineraries/%s/qr' % itinerary_id)
        data = resp.get_json()
        print(f"Status: {resp.status_code}")
        if data:
            print(f"QR URL Presence: {'qr_code_url' in data}")
    print("\n--- 3) GET /api/v1/events ---")
    resp = client.get('/api/v1/events')
    events = resp.get_json()
    print(f"Status: {resp.status_code}")
    if isinstance(events, list) and len(events) > 0:
        event = events[0]
        fields = ['image_url', 'venue', 'organizer', 'details_url', 'start_date', 'end_date']
        presence = {f: f in event for f in fields}
        print(f"First Event Fields Presence: {presence}")
        event_id = event.get('id')
        print("\n--- 4) GET /api/v1/events/%s ---" % event_id)
        resp = client.get('/api/v1/events/%s' % event_id)
        data = resp.get_json()
        print(f"Status: {resp.status_code}")
        if data:
            presence = {f: f in data for f in fields}
            print(f"Event Details Fields Presence: {presence}")
    print("\n--- 5) Transport ---")
    resp = client.get('/api/v1/transport/routes/')
    print(f"Routes Status: {resp.status_code}, Count: {len(resp.get_json()) if resp.status_code == 200 else 'N/A'}")
    resp = client.get('/api/v1/transport/schedules/')
    print(f"Schedules Status: {resp.status_code}, Count: {len(resp.get_json()) if resp.status_code == 200 else 'N/A'}")

if __name__ == "__main__":
    test_workflow()
