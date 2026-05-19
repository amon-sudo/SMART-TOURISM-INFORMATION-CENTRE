from app import create_app
from app.extensions import db
from app.user_settings.models.models import User
from app.Business.Business_registration.MVC_architecture_business.Business_registration_models.Business_registration_domain.Business_registration_domain import (
    BusinessRegistrationRequest,  # noqa: F401
)
from app.Business.Business_Profile.MVC_architecture.Business_profile_models.Business_profile_domain.Business_profile_domain import (
    BusinessProfile,
)
from app.tourism_amenitties.amenities.models.amenities import Amenity
from app.tourism_amenitties.destination.models.destination import Destination
from app.tourism_amenitties.attractions.models.attraction import Attraction
from app.tourism_amenitties.events.models.event import Event
from app.tourism_amenitties.attractions.models.product_profile import TourismProductProfile
from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_models.transport_stations_domain import (
    transport_station,
)
from app.transport_feature.Transport_routes.MVC_architecture.transport_routes_models.transport_routes_domain import (
    TransportRoute,
)
from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_domain import (
    transport_schedule,
)
from datetime import datetime, timedelta

app = create_app()


def _ensure_user(email: str, password: str = "password123") -> User:
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def _ensure_business_profile(user: User, business_name: str) -> BusinessProfile:
    profile = BusinessProfile.query.filter_by(user_id=user.id).first()
    if profile:
        return profile
    profile = BusinessProfile(
        user_id=user.id,
        business_name=business_name,
        business_type="tourism_operator",
        verified=True,
        is_active=True,
    )
    db.session.add(profile)
    db.session.flush()
    return profile


def _ensure_amenity(name: str, icon_url: str | None = None) -> Amenity:
    amenity = Amenity.query.filter_by(name=name).first()
    if amenity:
        return amenity
    amenity = Amenity(name=name, icon_url=icon_url)
    db.session.add(amenity)
    db.session.flush()
    return amenity


def _ensure_destination(data: dict) -> Destination:
    destination = Destination.query.filter_by(slug=data["slug"]).first()
    if destination:
        return destination
    destination = Destination(**data)
    db.session.add(destination)
    db.session.flush()
    return destination


def _ensure_attraction(data: dict, amenity_names: list[str]) -> Attraction:
    attraction = Attraction.query.filter_by(name=data["name"], destination_id=data["destination_id"]).first()
    if attraction:
        attraction.image_url = data.get("image_url")
        attraction.status = data.get("status")
        attraction.category = data.get("category")
        attraction.description = data.get("description")
        attraction.entry_fee = data.get("entry_fee")
        attraction.avg_rating = data.get("avg_rating")
        attraction.is_wheelchair_accessible = data.get("is_wheelchair_accessible", attraction.is_wheelchair_accessible)
        attraction.latitude = data.get("latitude")
        attraction.longitude = data.get("longitude")
        # Keep amenities synced without duplicating rows.
        existing_names = {a.name for a in attraction.amenities}
        for amenity_name in amenity_names:
            if amenity_name not in existing_names:
                attraction.amenities.append(_ensure_amenity(amenity_name))
        return attraction

    attraction = Attraction(**data)
    for amenity_name in amenity_names:
        attraction.amenities.append(_ensure_amenity(amenity_name))
    db.session.add(attraction)
    db.session.flush()
    return attraction


def _ensure_event(data: dict) -> Event:
    event = Event.query.filter_by(name=data["name"], destination_id=data["destination_id"]).first()
    if event:
        event.description = data.get("description")
        event.image_url = data.get("image_url")
        event.venue = data.get("venue")
        event.organizer = data.get("organizer")
        event.details_url = data.get("details_url")
        event.start_date = data.get("start_date")
        event.end_date = data.get("end_date")
        event.ticket_price = data.get("ticket_price", event.ticket_price)
        event.status = data.get("status", event.status)
        return event
    event = Event(**data)
    db.session.add(event)
    db.session.flush()
    return event


def _ensure_station(data: dict) -> transport_station:
    station = transport_station.query.filter_by(name=data["name"], city=data.get("city")).first()
    location = data.get("location")
    location_text = f"{location[0]},{location[1]}" if location else None
    if station:
        station.type = data["type"]
        station.street = data.get("street")
        station.city = data.get("city")
        station.region = data.get("region")
        station.country = data.get("country")
        station.location = location_text
        return station

    station = transport_station(
        name=data["name"],
        type=data["type"],
        street=data.get("street"),
        city=data.get("city"),
        region=data.get("region"),
        country=data.get("country"),
        location=location_text,
    )
    db.session.add(station)
    db.session.flush()
    return station


def _ensure_route(data: dict) -> TransportRoute:
    route = TransportRoute.query.filter_by(
        type=data["type"],
        origin_station_id=data["origin_station_id"],
        duration_minutes=data["duration_minutes"],
        base_fare=data["base_fare"],
    ).first()
    if route:
        route.is_active = data.get("is_active", True)
        return route

    route = TransportRoute(**data)
    db.session.add(route)
    db.session.flush()
    return route


def _ensure_schedule(data: dict) -> transport_schedule:
    schedule = transport_schedule.query.filter_by(
        transport_route_id=data["transport_route_id"],
        departure_time=data["departure_time"],
    ).first()
    if schedule:
        schedule.arrival_time = data["arrival_time"]
        schedule.available_seats = data["available_seats"]
        schedule.price = data["price"]
        schedule.is_active = data.get("is_active", True)
        return schedule

    max_numeric_id = db.session.query(db.func.max(transport_schedule.numeric_id)).scalar() or 0
    schedule = transport_schedule(
        numeric_id=max_numeric_id + 1,
        **data,
    )
    db.session.add(schedule)
    db.session.flush()
    return schedule


def _ensure_product_profile(attraction: Attraction, data: dict) -> TourismProductProfile:
    profile = TourismProductProfile.query.filter_by(attraction_id=attraction.id).first()
    if profile is None:
        profile = TourismProductProfile(attraction_id=attraction.id)
        db.session.add(profile)

    for field, value in data.items():
        setattr(profile, field, value)

    db.session.flush()
    return profile


def seed_data():
    with app.app_context():
        print("Seeding Kenyan tourism test data...")

        owner_user = _ensure_user("kenya.operator@example.com")
        owner_profile = _ensure_business_profile(owner_user, "Safari Horizons Kenya")

        destinations = [
            {
                "canonical_name": "Nairobi",
                "name": "Nairobi",
                "slug": "nairobi",
                "description": "Kenya's capital city, blending wildlife, culture, and urban experiences.",
                "overview_json": {"en": "A modern African city with nearby parks and museums."},
                "culture_json": {"en": "Home to diverse communities and vibrant arts."},
                "travel_tips_json": {"en": "Use ride-hailing apps and avoid peak-hour traffic."},
                "weather_info": {"best_months": ["Jan", "Feb", "Jun", "Jul", "Aug", "Sep"]},
                "is_wheelchair_accessible": True,
            },
            {
                "canonical_name": "Mombasa",
                "name": "Mombasa",
                "slug": "mombasa",
                "description": "Historic coastal city with beaches, Swahili culture, and marine life.",
                "overview_json": {"en": "A coastal destination known for old town heritage and beach resorts."},
                "culture_json": {"en": "Strong Swahili and Arab historical influences."},
                "travel_tips_json": {"en": "Stay hydrated and carry sun protection."},
                "weather_info": {"best_months": ["Jul", "Aug", "Sep", "Oct", "Dec"]},
                "is_wheelchair_accessible": True,
            },
            {
                "canonical_name": "Maasai Mara",
                "name": "Maasai Mara",
                "slug": "maasai-mara",
                "description": "World-renowned savannah reserve known for wildlife and migration.",
                "overview_json": {"en": "Top safari destination with rich biodiversity."},
                "culture_json": {"en": "Maasai communities with deep conservation heritage."},
                "travel_tips_json": {"en": "Book game drives early for migration season."},
                "weather_info": {"best_months": ["Jul", "Aug", "Sep", "Oct"]},
                "is_wheelchair_accessible": False,
            },
            {
                "canonical_name": "Naivasha",
                "name": "Naivasha",
                "slug": "naivasha",
                "description": "Rift Valley lake destination famous for birds, hippos, and day trips.",
                "overview_json": {"en": "Ideal for weekend escapes with lake and park activities."},
                "culture_json": {"en": "Agriculture and tourism shape local livelihoods."},
                "travel_tips_json": {"en": "Carry binoculars for birdwatching tours."},
                "weather_info": {"best_months": ["Jan", "Feb", "Jun", "Jul", "Aug"]},
                "is_wheelchair_accessible": True,
            },
        ]

        destination_map: dict[str, Destination] = {}
        for destination_data in destinations:
            destination = _ensure_destination(destination_data)
            destination_map[destination.slug] = destination

        attractions_payload = [
            {
                "name": "Nairobi National Park",
                "destination_slug": "nairobi",
                "description": "National park bordering the capital with lions, rhinos, and giraffes.",
                "image_url": "https://images.unsplash.com/photo-1549366021-9f761d450615?auto=format&fit=crop&w=1400&q=80",
                "category": "Wildlife",
                "latitude": -1.3733,
                "longitude": 36.8583,
                "status": "approved",
                "is_wheelchair_accessible": True,
                "entry_fee": 43.0,
                "avg_rating": 4.7,
                "amenities": ["Parking", "Guided Tours", "Restrooms"],
            },
            {
                "name": "Fort Jesus",
                "destination_slug": "mombasa",
                "description": "UNESCO heritage site that narrates Mombasa's coastal history.",
                "image_url": "https://images.unsplash.com/photo-1596803244618-8dbee441d70d?auto=format&fit=crop&w=1400&q=80",
                "category": "Heritage",
                "latitude": -4.0622,
                "longitude": 39.6772,
                "status": "approved",
                "is_wheelchair_accessible": True,
                "entry_fee": 12.0,
                "avg_rating": 4.4,
                "amenities": ["Museum Shop", "Guided Tours", "Restrooms"],
            },
            {
                "name": "Maasai Mara National Reserve",
                "destination_slug": "maasai-mara",
                "description": "Iconic reserve for the great wildebeest migration and big cats.",
                "image_url": "https://images.unsplash.com/photo-1516426122078-c23e76319801?auto=format&fit=crop&w=1400&q=80",
                "category": "Safari",
                "latitude": -1.4931,
                "longitude": 35.1439,
                "status": "approved",
                "is_wheelchair_accessible": False,
                "entry_fee": 80.0,
                "avg_rating": 4.9,
                "amenities": ["Game Drives", "Camping", "Picnic Sites"],
            },
            {
                "name": "Hell's Gate National Park",
                "destination_slug": "naivasha",
                "description": "Dramatic cliffs and gorges ideal for cycling and hiking safaris.",
                "image_url": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1400&q=80",
                "category": "Adventure",
                "latitude": -0.9067,
                "longitude": 36.3064,
                "status": "approved",
                "is_wheelchair_accessible": False,
                "entry_fee": 30.0,
                "avg_rating": 4.5,
                "amenities": ["Bike Rental", "Guided Hikes", "Parking"],
            },
            {
                "name": "Lake Naivasha Boat Safari",
                "destination_slug": "naivasha",
                "description": "Boat tours featuring hippos, fish eagles, and shoreline wildlife.",
                "image_url": "https://images.unsplash.com/photo-1472396961693-142e6e269027?auto=format&fit=crop&w=1400&q=80",
                "category": "Nature",
                "latitude": -0.7229,
                "longitude": 36.4319,
                "status": "approved",
                "is_wheelchair_accessible": True,
                "entry_fee": 25.0,
                "avg_rating": 4.3,
                "amenities": ["Life Jackets", "Guided Tours", "Family Friendly"],
            },
        ]

        attraction_map: dict[str, Attraction] = {}
        for attraction_data in attractions_payload:
            destination = destination_map[attraction_data["destination_slug"]]
            attraction_model_data = {
                "destination_id": destination.id,
                "business_owner_id": owner_profile.id,
                "name": attraction_data["name"],
                "description": attraction_data["description"],
                "image_url": attraction_data.get("image_url"),
                "category": attraction_data["category"],
                "latitude": attraction_data["latitude"],
                "longitude": attraction_data["longitude"],
                "status": attraction_data["status"],
                "is_wheelchair_accessible": attraction_data["is_wheelchair_accessible"],
                "entry_fee": attraction_data["entry_fee"],
                "avg_rating": attraction_data["avg_rating"],
            }
            attraction = _ensure_attraction(attraction_model_data, attraction_data["amenities"])
            attraction_map[attraction.name] = attraction

        profile_payload_by_attraction = {
            "Nairobi National Park": {
                "county": "Nairobi",
                "sub_county": "Lang'ata",
                "ward": "Nairobi West",
                "locality": "Lang'ata",
                "gps_coordinates": "-1.3733,36.8583",
                "unique_features": "Only national park bordering a capital city.",
                "conservation_efforts": "Rhino protection and habitat restoration programs.",
                "visitor_capacity": 2500,
                "experience_types": "guided,self-guided,game-drive",
                "average_stay_time": "2-4 hours",
                "best_visiting_period": "June to October",
                "key_events": "Wildlife conservation week",
                "infrastructure_status": {
                    "roads_access": "good",
                    "kiosks_ticketing": "available",
                    "fencing_security": "high",
                    "water_supply": "available",
                    "signage": "good",
                    "parking": "available",
                    "rest_areas": "available",
                },
                "site_status": "active",
                "tour_operators": "Safari Horizons Kenya, CityWild Tours",
                "nearby_accommodation": "Carnivore Hotel, Ole Sereni",
                "local_guides": "Certified KWS guides",
                "distance_to_hub": "12 km from Nairobi CBD",
            },
            "Fort Jesus": {
                "county": "Mombasa",
                "sub_county": "Mvita",
                "ward": "Old Town",
                "locality": "Mombasa Old Town",
                "gps_coordinates": "-4.0622,39.6772",
                "unique_features": "UNESCO World Heritage Portuguese fort.",
                "conservation_efforts": "Coastal heritage preservation and restoration.",
                "visitor_capacity": 900,
                "experience_types": "guided,self-guided,museum",
                "average_stay_time": "1-2 hours",
                "best_visiting_period": "July to October",
                "key_events": "Coastal Heritage Day",
                "infrastructure_status": {
                    "roads_access": "good",
                    "kiosks_ticketing": "available",
                    "fencing_security": "moderate",
                    "water_supply": "available",
                    "signage": "good",
                    "parking": "limited",
                    "rest_areas": "available",
                },
                "site_status": "active",
                "tour_operators": "Swahili Coast Tours",
                "nearby_accommodation": "Old Town Boutique Hotels",
                "local_guides": "Museum-certified heritage guides",
                "distance_to_hub": "2 km from Mombasa CBD",
            },
        }

        for attraction_name, profile_data in profile_payload_by_attraction.items():
            attraction = attraction_map.get(attraction_name)
            if attraction:
                _ensure_product_profile(attraction, profile_data)

        now = datetime.utcnow()
        events_payload = [
            {
                "name": "Nairobi Street Food & Culture Week",
                "destination_slug": "nairobi",
                "attraction_name": "Nairobi National Park",
                "description": "A week-long showcase of Kenyan cuisine, live music, artisan markets, and cultural performances across Nairobi.",
                "image_url": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1400&q=80",
                "venue": "Uhuru Park & Nairobi Street Corridors",
                "organizer": "Nairobi Tourism Board",
                "details_url": "https://example.com/events/nairobi-street-food-culture-week",
                "start_offset_days": 10,
                "end_offset_days": 12,
                "ticket_price": 15.0,
                "status": "scheduled",
            },
            {
                "name": "Mombasa Dhow Festival",
                "destination_slug": "mombasa",
                "attraction_name": "Fort Jesus",
                "description": "Traditional dhow races, Swahili dance performances, coastal cuisine popups, and a curated craft bazaar by local artisans.",
                "image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1400&q=80",
                "venue": "Old Port Waterfront, Mombasa",
                "organizer": "Coast Heritage & Tourism Council",
                "details_url": "https://example.com/events/mombasa-dhow-festival",
                "start_offset_days": 20,
                "end_offset_days": 22,
                "ticket_price": 20.0,
                "status": "scheduled",
            },
            {
                "name": "Great Mara Migration Viewing Camp",
                "destination_slug": "maasai-mara",
                "attraction_name": "Maasai Mara National Reserve",
                "description": "Guided migration viewing drives with ranger-led conservation briefings, sunrise photography sessions, and family-friendly nature talks.",
                "image_url": "https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?auto=format&fit=crop&w=1400&q=80",
                "venue": "Talek Gate Conservancy Camps",
                "organizer": "Mara Conservation Network",
                "details_url": "https://example.com/events/mara-migration-viewing-camp",
                "start_offset_days": 30,
                "end_offset_days": 35,
                "ticket_price": 65.0,
                "status": "scheduled",
            },
            {
                "name": "Naivasha Adventure & Birding Weekend",
                "destination_slug": "naivasha",
                "attraction_name": "Lake Naivasha Boat Safari",
                "description": "Weekend circuit of boat safaris, guided birdwatching, and cycling routes around Hell's Gate and Lake Naivasha ecosystems.",
                "image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1400&q=80",
                "venue": "Naivasha Waterfront Activity Zone",
                "organizer": "Rift Valley Eco Adventures",
                "details_url": "https://example.com/events/naivasha-adventure-birding-weekend",
                "start_offset_days": 14,
                "end_offset_days": 15,
                "ticket_price": 28.0,
                "status": "scheduled",
            },
        ]

        for event_data in events_payload:
            destination = destination_map[event_data["destination_slug"]]
            attraction = attraction_map.get(event_data["attraction_name"])
            event_model_data = {
                "destination_id": destination.id,
                "attraction_id": attraction.id if attraction else None,
                "name": event_data["name"],
                "description": event_data["description"],
                "image_url": event_data.get("image_url"),
                "venue": event_data.get("venue"),
                "organizer": event_data.get("organizer"),
                "details_url": event_data.get("details_url"),
                "start_date": now + timedelta(days=event_data["start_offset_days"]),
                "end_date": now + timedelta(days=event_data["end_offset_days"]),
                "ticket_price": event_data["ticket_price"],
                "status": event_data["status"],
            }
            _ensure_event(event_model_data)

        stations_payload = [
            {
                "name": "Nairobi Railway Station",
                "type": "train_station",
                "street": "Haile Selassie Ave",
                "city": "Nairobi",
                "region": "Nairobi County",
                "country": "Kenya",
                "location": (-1.2921, 36.8219),
            },
            {
                "name": "Nairobi Central Bus Terminal",
                "type": "bus_terminal",
                "street": "Landhies Rd",
                "city": "Nairobi",
                "region": "Nairobi County",
                "country": "Kenya",
                "location": (-1.2869, 36.8285),
            },
            {
                "name": "Mombasa SGR Terminus",
                "type": "train_station",
                "street": "Miritini",
                "city": "Mombasa",
                "region": "Mombasa County",
                "country": "Kenya",
                "location": (-4.0333, 39.6167),
            },
        ]

        station_map: dict[str, transport_station] = {}
        for station_data in stations_payload:
            station = _ensure_station(station_data)
            station_map[station.name] = station

        routes_payload = [
            {
                "type": "train",
                "origin_station_name": "Nairobi Railway Station",
                "duration_minutes": 330,
                "base_fare": 1200.0,
            },
            {
                "type": "bus",
                "origin_station_name": "Nairobi Central Bus Terminal",
                "duration_minutes": 540,
                "base_fare": 1800.0,
            },
            {
                "type": "shuttle",
                "origin_station_name": "Nairobi Central Bus Terminal",
                "duration_minutes": 120,
                "base_fare": 600.0,
            },
            {
                "type": "flight",
                "origin_station_name": "Nairobi Railway Station",
                "duration_minutes": 60,
                "base_fare": 9500.0,
            },
            {
                "type": "bus",
                "origin_station_name": "Mombasa SGR Terminus",
                "duration_minutes": 45,
                "base_fare": 350.0,
            },
        ]

        route_map: dict[str, TransportRoute] = {}
        for index, route_data in enumerate(routes_payload, start=1):
            origin_station = station_map[route_data["origin_station_name"]]
            route = _ensure_route(
                {
                    "type": route_data["type"],
                    "origin_station_id": origin_station.id,
                    "duration_minutes": route_data["duration_minutes"],
                    "base_fare": route_data["base_fare"],
                    "is_active": True,
                }
            )
            route_map[f"route_{index}"] = route

        base_departure = datetime.utcnow().replace(hour=7, minute=0, second=0, microsecond=0)
        schedules_payload = [
            {
                "route_key": "route_1",
                "departure_offset_hours": 0,
                "duration_minutes": 330,
                "available_seats": 220,
                "price": 1200.0,
            },
            {
                "route_key": "route_2",
                "departure_offset_hours": 1,
                "duration_minutes": 540,
                "available_seats": 45,
                "price": 1800.0,
            },
            {
                "route_key": "route_3",
                "departure_offset_hours": 2,
                "duration_minutes": 120,
                "available_seats": 14,
                "price": 600.0,
            },
            {
                "route_key": "route_1",
                "departure_offset_hours": 8,
                "duration_minutes": 330,
                "available_seats": 210,
                "price": 1300.0,
            },
            {
                "route_key": "route_4",
                "departure_offset_hours": 3,
                "duration_minutes": 60,
                "available_seats": 72,
                "price": 9800.0,
            },
            {
                "route_key": "route_2",
                "departure_offset_hours": 10,
                "duration_minutes": 540,
                "available_seats": 38,
                "price": 1750.0,
            },
            {
                "route_key": "route_5",
                "departure_offset_hours": 4,
                "duration_minutes": 45,
                "available_seats": 32,
                "price": 350.0,
            },
            {
                "route_key": "route_3",
                "departure_offset_hours": 7,
                "duration_minutes": 120,
                "available_seats": 12,
                "price": 650.0,
            },
        ]

        for schedule_data in schedules_payload:
            route = route_map[schedule_data["route_key"]]
            departure = base_departure + timedelta(hours=schedule_data["departure_offset_hours"])
            arrival = departure + timedelta(minutes=schedule_data["duration_minutes"])
            _ensure_schedule(
                {
                    "transport_route_id": route.id,
                    "departure_time": departure,
                    "arrival_time": arrival,
                    "available_seats": schedule_data["available_seats"],
                    "price": schedule_data["price"],
                    "is_active": True,
                }
            )

        db.session.commit()

        print("Kenyan seed data is ready.")
        print(f"Destinations: {Destination.query.count()}")
        print(f"Attractions: {Attraction.query.count()}")
        print(f"Events: {Event.query.count()}")
        print(f"Amenities: {Amenity.query.count()}")
        print(f"Stations: {transport_station.query.count()}")
        print(f"Transport routes: {TransportRoute.query.count()}")
        print(f"Transport schedules: {transport_schedule.query.count()}")
        print(f"Tourism product profiles: {TourismProductProfile.query.count()}")
        print(f"Seed business owner: {owner_user.email}")

if __name__ == "__main__":
    seed_data()
