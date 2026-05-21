from app import create_app
from app.extensions import db

# create_app() registers all blueprints and therefore imports every model in
# the correct dependency order.  Subsequent imports then resolve cleanly.
app = create_app()

from app.user_settings.models.models import User  # noqa: E402
from app.Business.Business_Profile.MVC_architecture.Business_profile_models.Business_profile_domain.Business_profile_domain import (  # noqa: E402
    BusinessProfile,
)
from app.tourism_amenitties.amenities.models.amenities import Amenity  # noqa: E402
from app.tourism_amenitties.destination.models.destination import Destination  # noqa: E402
from app.tourism_amenitties.attractions.models.attraction import Attraction  # noqa: E402
from app.tourism_amenitties.events.models.event import Event  # noqa: E402
from app.tourism_amenitties.attractions.models.product_profile import TourismProductProfile  # noqa: E402
from app.tourism_amenitties.accommodation.models.accommodation import Accommodation, RoomType  # noqa: E402
from app.tourism_amenitties.tours.models.tour_package import TourPackage  # noqa: E402
from app.feedback_media.models import EmergencyContact  # noqa: E402
from app.transport_feature.Transport_stations.MVC_architecture.transport_stations_models.transport_stations_domain import (  # noqa: E402
    transport_station,
)
from app.transport_feature.Transport_routes.MVC_architecture.transport_routes_models.transport_routes_domain import (  # noqa: E402
    TransportRoute,
)
from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_domain import (  # noqa: E402
    transport_schedule,
)
from app.kiosk_feature.kiosk.MVC_architecture.models.kiosk import Kiosk, KioskStatus, KioskLocationType  # noqa: E402
from app.booking_feature.models.booking import (  # noqa: E402
    Booking, BookingItem, BookingStatus, BookingType, BookingItemTargetType, RefundStatus,
)
from datetime import datetime, timedelta, time  # noqa: E402


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ensure_user(email: str, password: str = "password123", username: str | None = None) -> User:
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(email=email, username=username or email.split("@")[0])
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


def _ensure_accommodation(attraction: Attraction, data: dict) -> Accommodation:
    acc = Accommodation.query.filter_by(attraction_id=attraction.id).first()
    if acc:
        acc.star_rating = data.get("star_rating", acc.star_rating)
        acc.check_in_time = data.get("check_in_time", acc.check_in_time)
        acc.check_out_time = data.get("check_out_time", acc.check_out_time)
        acc.policies = data.get("policies", acc.policies)
        return acc

    acc = Accommodation(
        attraction_id=attraction.id,
        star_rating=data.get("star_rating", 3),
        check_in_time=data.get("check_in_time"),
        check_out_time=data.get("check_out_time"),
        policies=data.get("policies"),
    )
    db.session.add(acc)
    db.session.flush()
    return acc


def _ensure_room_type(accommodation: Accommodation, name: str, data: dict) -> RoomType:
    room = RoomType.query.filter_by(accommodation_id=accommodation.id, name=name).first()
    if room:
        room.base_price = data.get("base_price", room.base_price)
        room.capacity = data.get("capacity", room.capacity)
        room.amenities_json = data.get("amenities_json", room.amenities_json)
        return room

    room = RoomType(
        accommodation_id=accommodation.id,
        name=name,
        base_price=data["base_price"],
        capacity=data.get("capacity", 2),
        amenities_json=data.get("amenities_json", {}),
    )
    db.session.add(room)
    db.session.flush()
    return room


def _ensure_kiosk(business_profile: BusinessProfile, data: dict) -> Kiosk:
    kiosk = Kiosk.query.filter_by(name=data["name"]).first()
    if kiosk:
        kiosk.status = data.get("status", kiosk.status)
        kiosk.address = data.get("address", kiosk.address)
        kiosk.location_type = data.get("location_type", kiosk.location_type)
        kiosk.configuration = data.get("configuration", kiosk.configuration)
        return kiosk

    loc = data.get("location")
    kiosk = Kiosk(
        business_profile_id=business_profile.id,
        name=data["name"],
        location=f"{loc[0]},{loc[1]}" if loc else None,
        address=data.get("address"),
        location_type=data["location_type"],
        status=data.get("status", KioskStatus.ACTIVE),
        last_heartbeat_at=datetime.utcnow() - timedelta(minutes=2),
        installed_at=datetime.utcnow() - timedelta(days=data.get("installed_days_ago", 90)),
        configuration=data.get("configuration", {
            "screen_brightness": 80,
            "idle_timeout_seconds": 120,
            "enabled_languages": ["en", "sw"],
            "default_language": "en",
            "show_booking": True,
            "show_emergency": True,
            "theme": "default",
        }),
    )
    db.session.add(kiosk)
    db.session.flush()
    return kiosk


def _ensure_tour_package(business_profile: BusinessProfile, data: dict) -> TourPackage:
    pkg = TourPackage.query.filter_by(name=data["name"], operator_id=business_profile.id).first()
    if pkg:
        pkg.description = data.get("description", pkg.description)
        pkg.duration_days = data.get("duration_days", pkg.duration_days)
        pkg.price = data.get("price", pkg.price)
        pkg.max_participants = data.get("max_participants", pkg.max_participants)
        pkg.status = data.get("status", pkg.status)
        return pkg

    pkg = TourPackage(
        operator_id=business_profile.id,
        name=data["name"],
        description=data.get("description"),
        duration_days=data["duration_days"],
        price=data["price"],
        max_participants=data.get("max_participants", 10),
        status=data.get("status", "active"),
    )
    db.session.add(pkg)
    db.session.flush()
    return pkg


def _ensure_emergency_contact(destination: Destination, name: str, data: dict) -> EmergencyContact:
    contact = EmergencyContact.query.filter_by(
        destination_id=destination.id, name=name
    ).first()
    if contact:
        contact.type = data.get("type", contact.type)
        contact.phone = data.get("phone", contact.phone)
        contact.city = data.get("city", contact.city)
        contact.region = data.get("region", contact.region)
        return contact

    contact = EmergencyContact(
        destination_id=destination.id,
        name=name,
        type=data.get("type"),
        phone=data.get("phone"),
        street=data.get("street"),
        city=data.get("city"),
        region=data.get("region"),
    )
    db.session.add(contact)
    db.session.flush()
    return contact


def _ensure_booking(user: User, data: dict, items: list[dict]) -> Booking:
    """Create a booking with items if a booking with the same reference_number doesn't exist."""
    ref = data["reference_number"]
    booking = Booking.query.filter_by(reference_number=ref).first()
    if booking:
        return booking

    booking = Booking(
        user_id=user.id,
        kiosk_id=data.get("kiosk_id"),
        reference_number=ref,
        type=data["type"],
        status=data.get("status", BookingStatus.CONFIRMED),
        total_cost=data["total_cost"],
        refund_status=data.get("refund_status", RefundStatus.NONE),
        cancelled_at=data.get("cancelled_at"),
        cancellation_reason=data.get("cancellation_reason"),
    )
    db.session.add(booking)
    db.session.flush()

    for item in items:
        db.session.add(BookingItem(
            booking_id=booking.id,
            target_type=item["target_type"],
            target_id=item["target_id"],
            quantity=item.get("quantity", 1),
            price_at_booking=item["price_at_booking"],
            notes=item.get("notes"),
        ))
    db.session.flush()
    return booking


# ─── Main seed function ───────────────────────────────────────────────────────

def seed_data():
    with app.app_context():
        print("Seeding Kenyan tourism test data...")

        # ── Users ──────────────────────────────────────────────────────────────
        owner_user = _ensure_user("kenya.operator@example.com", username="safarihorizons")
        tourist_user = _ensure_user("tourist@example.com", password="Tourist123!", username="alice_tourist")
        admin_user = _ensure_user("admin@example.com", password="Admin1234!", username="admin_kenya")

        owner_profile = _ensure_business_profile(owner_user, "Safari Horizons Kenya")
        _ensure_business_profile(admin_user, "Kenya Tourism Board")

        # ── Destinations ────────────────────────────────────────────────────────
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
            {
                "canonical_name": "Amboseli",
                "name": "Amboseli",
                "slug": "amboseli",
                "description": "Iconic park at the foot of Mt Kilimanjaro, famous for large elephant herds.",
                "overview_json": {"en": "Best views of Kilimanjaro with huge elephant herds."},
                "culture_json": {"en": "Maasai culture and eco-tourism at the forefront."},
                "travel_tips_json": {"en": "Visit at sunrise for Kilimanjaro backdrop."},
                "weather_info": {"best_months": ["Jun", "Oct"]},
                "is_wheelchair_accessible": False,
            },
        ]

        destination_map: dict[str, Destination] = {}
        for destination_data in destinations:
            destination = _ensure_destination(destination_data)
            destination_map[destination.slug] = destination

        # ── Attractions ─────────────────────────────────────────────────────────
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
                "name": "Nairobi Safari Club Hotel",
                "destination_slug": "nairobi",
                "description": "Luxury hotel in Nairobi city centre with rooftop pool and safari-themed rooms.",
                "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1400&q=80",
                "category": "Hotel",
                "latitude": -1.2884,
                "longitude": 36.8233,
                "status": "approved",
                "is_wheelchair_accessible": True,
                "entry_fee": 0.0,
                "avg_rating": 4.5,
                "amenities": ["WiFi", "Pool", "Restaurant", "Bar", "Parking", "Gym", "Spa"],
            },
            {
                "name": "Ole Sereni Hotel",
                "destination_slug": "nairobi",
                "description": "Boutique hotel overlooking the Nairobi National Park. Wildlife views from every room.",
                "image_url": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1400&q=80",
                "category": "Hotel",
                "latitude": -1.3521,
                "longitude": 36.8472,
                "status": "approved",
                "is_wheelchair_accessible": True,
                "entry_fee": 0.0,
                "avg_rating": 4.6,
                "amenities": ["WiFi", "Pool", "Restaurant", "Bar", "Parking", "Game Viewing"],
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
                "name": "Diani Reef Beach Resort & Spa",
                "destination_slug": "mombasa",
                "description": "Award-winning beachfront resort on the white sands of Diani Beach.",
                "image_url": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1400&q=80",
                "category": "Hotel",
                "latitude": -4.3167,
                "longitude": 39.5667,
                "status": "approved",
                "is_wheelchair_accessible": True,
                "entry_fee": 0.0,
                "avg_rating": 4.8,
                "amenities": ["WiFi", "Pool", "Beach Access", "Restaurant", "Bar", "Spa", "Watersports"],
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
                "name": "Mara Serena Safari Lodge",
                "destination_slug": "maasai-mara",
                "description": "Iconic hilltop lodge inside the Maasai Mara with panoramic bush views.",
                "image_url": "https://images.unsplash.com/photo-1504150558240-0b4fd8946624?auto=format&fit=crop&w=1400&q=80",
                "category": "Hotel",
                "latitude": -1.5167,
                "longitude": 35.1833,
                "status": "approved",
                "is_wheelchair_accessible": False,
                "entry_fee": 0.0,
                "avg_rating": 4.7,
                "amenities": ["WiFi", "Pool", "Restaurant", "Bar", "Game Drives", "Bush Walks"],
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
                "name": "Lake Naivasha Sopa Resort",
                "destination_slug": "naivasha",
                "description": "Eco-friendly lakeside resort surrounded by yellow-bark acacia forest.",
                "image_url": "https://images.unsplash.com/photo-1501117716987-c8c394bb29df?auto=format&fit=crop&w=1400&q=80",
                "category": "Hotel",
                "latitude": -0.7500,
                "longitude": 36.3833,
                "status": "approved",
                "is_wheelchair_accessible": True,
                "entry_fee": 0.0,
                "avg_rating": 4.4,
                "amenities": ["WiFi", "Pool", "Restaurant", "Boat Rides", "Nature Walks", "Bird Watching"],
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
            {
                "name": "Amboseli Serena Safari Lodge",
                "destination_slug": "amboseli",
                "description": "Luxury lodge at the foot of Mt Kilimanjaro with elephant herds passing through daily.",
                "image_url": "https://images.unsplash.com/photo-1523805009345-7448845a9e53?auto=format&fit=crop&w=1400&q=80",
                "category": "Hotel",
                "latitude": -2.6333,
                "longitude": 37.2500,
                "status": "approved",
                "is_wheelchair_accessible": True,
                "entry_fee": 0.0,
                "avg_rating": 4.8,
                "amenities": ["WiFi", "Pool", "Restaurant", "Bar", "Game Drives", "Kilimanjaro View"],
            },
            {
                "name": "Amboseli National Park",
                "destination_slug": "amboseli",
                "description": "Famous park at the base of Kilimanjaro, known for large free-ranging elephants.",
                "image_url": "https://images.unsplash.com/photo-1551632811-561732d1e306?auto=format&fit=crop&w=1400&q=80",
                "category": "Wildlife",
                "latitude": -2.6520,
                "longitude": 37.2604,
                "status": "approved",
                "is_wheelchair_accessible": False,
                "entry_fee": 60.0,
                "avg_rating": 4.8,
                "amenities": ["Game Drives", "Picnic Sites", "Bird Watching"],
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

        # ── Tourism Product Profiles ─────────────────────────────────────────────
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
                    "roads": "good",
                    "visitor_center": "available",
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
                    "roads": "good",
                    "visitor_center": "available",
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

        # ── Events ──────────────────────────────────────────────────────────────
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
                "description": "Traditional dhow races, Swahili dance performances, coastal cuisine popups, and a curated craft bazaar.",
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
                "description": "Guided migration viewing drives with ranger-led conservation briefings and sunrise photography sessions.",
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
                "description": "Weekend circuit of boat safaris, guided birdwatching, and cycling routes around Hell's Gate.",
                "image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1400&q=80",
                "venue": "Naivasha Waterfront Activity Zone",
                "organizer": "Rift Valley Eco Adventures",
                "details_url": "https://example.com/events/naivasha-adventure-birding-weekend",
                "start_offset_days": 14,
                "end_offset_days": 15,
                "ticket_price": 28.0,
                "status": "scheduled",
            },
            {
                "name": "Kilimanjaro Elephant Safari",
                "destination_slug": "amboseli",
                "attraction_name": "Amboseli National Park",
                "description": "Sunrise and sunset game drives tracking Amboseli's famous elephant herds with Kilimanjaro as backdrop.",
                "image_url": "https://images.unsplash.com/photo-1564760055775-d63b17a55c44?auto=format&fit=crop&w=1400&q=80",
                "venue": "Amboseli National Park",
                "organizer": "KWS & Amboseli Eco Tours",
                "details_url": "https://example.com/events/kilimanjaro-elephant-safari",
                "start_offset_days": 7,
                "end_offset_days": 9,
                "ticket_price": 50.0,
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

        # ── Accommodations ──────────────────────────────────────────────────────
        print("Seeding accommodations...")
        accommodation_map: dict[str, Accommodation] = {}

        hotel_data = [
            {
                "attraction_name": "Nairobi Safari Club Hotel",
                "star_rating": 4,
                "check_in_time": time(14, 0),
                "check_out_time": time(11, 0),
                "policies": "Check-in from 2 PM. Early check-in subject to availability. No pets allowed. Free cancellation up to 48 hours before arrival.",
                "rooms": [
                    {
                        "name": "Standard Room",
                        "base_price": 120.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "safe": True},
                    },
                    {
                        "name": "Deluxe City View Room",
                        "base_price": 180.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "safe": True, "minibar": True, "city_view": True},
                    },
                    {
                        "name": "Executive Suite",
                        "base_price": 350.0,
                        "capacity": 3,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "safe": True, "minibar": True, "lounge_access": True, "jacuzzi": True},
                    },
                ],
            },
            {
                "attraction_name": "Ole Sereni Hotel",
                "star_rating": 4,
                "check_in_time": time(14, 0),
                "check_out_time": time(10, 0),
                "policies": "Check-in from 2 PM. All rooms overlook Nairobi National Park. Complimentary wildlife viewing binoculars provided.",
                "rooms": [
                    {
                        "name": "Park View Room",
                        "base_price": 200.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "park_view": True, "balcony": True},
                    },
                    {
                        "name": "Premium Park View Room",
                        "base_price": 280.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "park_view": True, "balcony": True, "minibar": True},
                    },
                    {
                        "name": "Junior Suite",
                        "base_price": 420.0,
                        "capacity": 3,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "park_view": True, "balcony": True, "minibar": True, "lounge_access": True},
                    },
                ],
            },
            {
                "attraction_name": "Diani Reef Beach Resort & Spa",
                "star_rating": 5,
                "check_in_time": time(15, 0),
                "check_out_time": time(11, 0),
                "policies": "Check-in from 3 PM. Beachfront property. All-inclusive packages available. Complimentary snorkelling gear for in-house guests.",
                "rooms": [
                    {
                        "name": "Garden Room",
                        "base_price": 160.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "garden_view": True},
                    },
                    {
                        "name": "Ocean View Room",
                        "base_price": 260.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "ocean_view": True, "balcony": True},
                    },
                    {
                        "name": "Beach Front Suite",
                        "base_price": 480.0,
                        "capacity": 4,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "ocean_view": True, "balcony": True, "private_plunge_pool": True},
                    },
                    {
                        "name": "Penthouse Suite",
                        "base_price": 750.0,
                        "capacity": 4,
                        "amenities_json": {"wifi": True, "ac": True, "tv": True, "ocean_view": True, "private_terrace": True, "private_plunge_pool": True, "butler_service": True},
                    },
                ],
            },
            {
                "attraction_name": "Mara Serena Safari Lodge",
                "star_rating": 4,
                "check_in_time": time(14, 0),
                "check_out_time": time(10, 0),
                "policies": "Full board included. Game drives at 06:00 and 16:00 daily. Bush dinners available on request.",
                "rooms": [
                    {
                        "name": "Standard Room",
                        "base_price": 300.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": False, "ac": False, "fan": True, "mosquito_net": True, "bush_view": True},
                    },
                    {
                        "name": "Superior Room",
                        "base_price": 420.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": False, "fan": True, "mosquito_net": True, "bush_view": True, "balcony": True},
                    },
                    {
                        "name": "Presidential Suite",
                        "base_price": 900.0,
                        "capacity": 4,
                        "amenities_json": {"wifi": True, "ac": True, "fan": True, "mosquito_net": True, "panoramic_view": True, "private_deck": True},
                    },
                ],
            },
            {
                "attraction_name": "Lake Naivasha Sopa Resort",
                "star_rating": 3,
                "check_in_time": time(14, 0),
                "check_out_time": time(10, 0),
                "policies": "Check-in from 2 PM. Lakeside property. Complimentary boat rides for in-house guests. Children welcome.",
                "rooms": [
                    {
                        "name": "Standard Cottage",
                        "base_price": 90.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": False, "fan": True, "lake_view": True},
                    },
                    {
                        "name": "Lake View Cottage",
                        "base_price": 140.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": False, "fan": True, "lake_view": True, "private_patio": True},
                    },
                    {
                        "name": "Family Cottage",
                        "base_price": 200.0,
                        "capacity": 4,
                        "amenities_json": {"wifi": True, "ac": False, "fan": True, "lake_view": True, "private_patio": True, "bunk_beds": True},
                    },
                ],
            },
            {
                "attraction_name": "Amboseli Serena Safari Lodge",
                "star_rating": 5,
                "check_in_time": time(15, 0),
                "check_out_time": time(11, 0),
                "policies": "Full board. Game drives twice daily. Spa and wellness centre on site. Children 5+ only.",
                "rooms": [
                    {
                        "name": "Standard Room",
                        "base_price": 380.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": True, "fan": True, "kilimanjaro_view": True},
                    },
                    {
                        "name": "Deluxe Room",
                        "base_price": 520.0,
                        "capacity": 2,
                        "amenities_json": {"wifi": True, "ac": True, "fan": True, "kilimanjaro_view": True, "balcony": True, "minibar": True},
                    },
                    {
                        "name": "Kilimanjaro Suite",
                        "base_price": 1100.0,
                        "capacity": 3,
                        "amenities_json": {"wifi": True, "ac": True, "fan": True, "panoramic_kilimanjaro_view": True, "private_deck": True, "butler_service": True},
                    },
                ],
            },
        ]

        for hotel in hotel_data:
            attraction = attraction_map.get(hotel["attraction_name"])
            if not attraction:
                print(f"  Warning: attraction '{hotel['attraction_name']}' not found, skipping")
                continue
            acc = _ensure_accommodation(attraction, hotel)
            accommodation_map[hotel["attraction_name"]] = acc
            for room_data in hotel["rooms"]:
                _ensure_room_type(acc, room_data["name"], room_data)
        print(f"  Accommodations: {Accommodation.query.count()}, Room types: {RoomType.query.count()}")

        # ── Transport ────────────────────────────────────────────────────────────
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
            {
                "name": "JKIA Airport",
                "type": "airport",
                "street": "Airport North Rd",
                "city": "Nairobi",
                "region": "Nairobi County",
                "country": "Kenya",
                "location": (-1.3192, 36.9275),
            },
            {
                "name": "Mombasa Moi International Airport",
                "type": "airport",
                "street": "Airport Rd",
                "city": "Mombasa",
                "region": "Mombasa County",
                "country": "Kenya",
                "location": (-4.0348, 39.5942),
            },
            {
                "name": "Naivasha Bus Stop",
                "type": "bus_terminal",
                "street": "Moi South Lake Rd",
                "city": "Naivasha",
                "region": "Nakuru County",
                "country": "Kenya",
                "location": (-0.7167, 36.4333),
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
                "origin_station_name": "JKIA Airport",
                "duration_minutes": 55,
                "base_fare": 9500.0,
            },
            {
                "type": "bus",
                "origin_station_name": "Mombasa SGR Terminus",
                "duration_minutes": 45,
                "base_fare": 350.0,
            },
            {
                "type": "shuttle",
                "origin_station_name": "Nairobi Central Bus Terminal",
                "duration_minutes": 90,
                "base_fare": 500.0,
            },
            {
                "type": "flight",
                "origin_station_name": "Mombasa Moi International Airport",
                "duration_minutes": 55,
                "base_fare": 8800.0,
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
            {"route_key": "route_1", "departure_offset_hours": 0, "duration_minutes": 330, "available_seats": 220, "price": 1200.0},
            {"route_key": "route_2", "departure_offset_hours": 1, "duration_minutes": 540, "available_seats": 45, "price": 1800.0},
            {"route_key": "route_3", "departure_offset_hours": 2, "duration_minutes": 120, "available_seats": 14, "price": 600.0},
            {"route_key": "route_1", "departure_offset_hours": 8, "duration_minutes": 330, "available_seats": 210, "price": 1300.0},
            {"route_key": "route_4", "departure_offset_hours": 3, "duration_minutes": 55, "available_seats": 72, "price": 9800.0},
            {"route_key": "route_2", "departure_offset_hours": 10, "duration_minutes": 540, "available_seats": 38, "price": 1750.0},
            {"route_key": "route_5", "departure_offset_hours": 4, "duration_minutes": 45, "available_seats": 32, "price": 350.0},
            {"route_key": "route_3", "departure_offset_hours": 7, "duration_minutes": 120, "available_seats": 12, "price": 650.0},
            {"route_key": "route_6", "departure_offset_hours": 5, "duration_minutes": 90, "available_seats": 16, "price": 500.0},
            {"route_key": "route_7", "departure_offset_hours": 6, "duration_minutes": 55, "available_seats": 85, "price": 9200.0},
            {"route_key": "route_4", "departure_offset_hours": 12, "duration_minutes": 55, "available_seats": 68, "price": 9500.0},
        ]

        schedule_map: dict[str, transport_schedule] = {}
        for idx, schedule_data in enumerate(schedules_payload):
            route = route_map[schedule_data["route_key"]]
            departure = base_departure + timedelta(hours=schedule_data["departure_offset_hours"])
            arrival = departure + timedelta(minutes=schedule_data["duration_minutes"])
            schedule = _ensure_schedule(
                {
                    "transport_route_id": route.id,
                    "departure_time": departure,
                    "arrival_time": arrival,
                    "available_seats": schedule_data["available_seats"],
                    "price": schedule_data["price"],
                    "is_active": True,
                }
            )
            schedule_map[f"sched_{idx}"] = schedule

        # ── Kiosks ──────────────────────────────────────────────────────────────
        print("Seeding kiosks...")
        kiosks_payload = [
            {
                "name": "JKIA Terminal 1 Kiosk",
                "location": (-1.3192, 36.9275),
                "address": "Jomo Kenyatta International Airport, Terminal 1, Nairobi",
                "location_type": KioskLocationType.AIRPORT,
                "status": KioskStatus.ACTIVE,
                "installed_days_ago": 120,
                "configuration": {
                    "screen_brightness": 90,
                    "idle_timeout_seconds": 90,
                    "enabled_languages": ["en", "sw", "fr", "zh"],
                    "default_language": "en",
                    "show_booking": True,
                    "show_emergency": True,
                    "theme": "airport",
                },
            },
            {
                "name": "Nairobi SGR Station Kiosk",
                "location": (-1.2921, 36.8219),
                "address": "Nairobi Railway Station, Haile Selassie Ave, Nairobi",
                "location_type": KioskLocationType.SGR_STATION,
                "status": KioskStatus.ACTIVE,
                "installed_days_ago": 90,
                "configuration": {
                    "screen_brightness": 80,
                    "idle_timeout_seconds": 120,
                    "enabled_languages": ["en", "sw"],
                    "default_language": "en",
                    "show_booking": True,
                    "show_emergency": True,
                    "theme": "default",
                },
            },
            {
                "name": "Maasai Mara Gate Kiosk",
                "location": (-1.4931, 35.1439),
                "address": "Sekenani Gate, Maasai Mara National Reserve, Narok",
                "location_type": KioskLocationType.NATIONAL_PARK,
                "status": KioskStatus.ACTIVE,
                "installed_days_ago": 60,
                "configuration": {
                    "screen_brightness": 85,
                    "idle_timeout_seconds": 180,
                    "enabled_languages": ["en", "sw"],
                    "default_language": "en",
                    "show_booking": True,
                    "show_emergency": True,
                    "theme": "wildlife",
                },
            },
            {
                "name": "Mombasa Old Town Kiosk",
                "location": (-4.0622, 39.6772),
                "address": "Fort Jesus, Old Town, Mombasa",
                "location_type": KioskLocationType.MUSEUM,
                "status": KioskStatus.ACTIVE,
                "installed_days_ago": 75,
                "configuration": {
                    "screen_brightness": 75,
                    "idle_timeout_seconds": 120,
                    "enabled_languages": ["en", "sw", "ar"],
                    "default_language": "en",
                    "show_booking": True,
                    "show_emergency": True,
                    "theme": "heritage",
                },
            },
            {
                "name": "Nairobi CBD Kiosk",
                "location": (-1.2921, 36.8219),
                "address": "Kenyatta Avenue, Nairobi CBD",
                "location_type": KioskLocationType.URBAN_CENTRE,
                "status": KioskStatus.MAINTENANCE,
                "installed_days_ago": 180,
                "configuration": {
                    "screen_brightness": 80,
                    "idle_timeout_seconds": 120,
                    "enabled_languages": ["en", "sw"],
                    "default_language": "en",
                    "show_booking": True,
                    "show_emergency": True,
                    "theme": "default",
                },
            },
            {
                "name": "Diani Beach Hotel Kiosk",
                "location": (-4.3167, 39.5667),
                "address": "Diani Beach Road, Kwale County",
                "location_type": KioskLocationType.HOTEL,
                "status": KioskStatus.ACTIVE,
                "installed_days_ago": 45,
                "configuration": {
                    "screen_brightness": 80,
                    "idle_timeout_seconds": 150,
                    "enabled_languages": ["en", "sw", "de", "it"],
                    "default_language": "en",
                    "show_booking": True,
                    "show_emergency": True,
                    "theme": "beach",
                },
            },
        ]

        kiosk_map: dict[str, Kiosk] = {}
        for kiosk_data in kiosks_payload:
            kiosk = _ensure_kiosk(owner_profile, kiosk_data)
            kiosk_map[kiosk_data["name"]] = kiosk
        print(f"  Kiosks: {Kiosk.query.count()}")

        # ── Tour Packages ────────────────────────────────────────────────────────
        print("Seeding tour packages...")
        tour_packages_payload = [
            {
                "name": "Mara Migration Safari — 5 Days",
                "description": "Experience the greatest wildlife spectacle on Earth. This 5-day package includes full-board accommodation at Mara Serena Lodge, twice-daily game drives, and a Maasai village cultural visit.",
                "duration_days": 5,
                "price": 1850.0,
                "max_participants": 8,
                "status": "active",
            },
            {
                "name": "Nairobi & Naivasha Weekend — 3 Days",
                "description": "Perfect weekend escape combining Nairobi National Park morning game drive, Lake Naivasha boat safari, and Hell's Gate cycling — all from Nairobi.",
                "duration_days": 3,
                "price": 480.0,
                "max_participants": 12,
                "status": "active",
            },
            {
                "name": "Kenya Coastal Escape — 7 Days",
                "description": "7-day luxury coastal package: Fort Jesus history tour, Diani Beach snorkelling, dhow cruise, and Wasini Island dolphin watching. Full board at Diani Reef Resort.",
                "duration_days": 7,
                "price": 2200.0,
                "max_participants": 10,
                "status": "active",
            },
            {
                "name": "Amboseli Elephant Safari — 4 Days",
                "description": "Marvel at Kilimanjaro and Africa's largest free-ranging elephant herds. 4 days full board at Amboseli Serena Lodge with expert naturalist guides.",
                "duration_days": 4,
                "price": 1400.0,
                "max_participants": 6,
                "status": "active",
            },
            {
                "name": "Kenya Grand Circuit — 10 Days",
                "description": "The ultimate Kenya experience: Nairobi, Amboseli, Maasai Mara, Lake Nakuru, and Mombasa. Luxury lodges throughout, all transfers included.",
                "duration_days": 10,
                "price": 4500.0,
                "max_participants": 8,
                "status": "active",
            },
        ]

        tour_package_map: dict[str, TourPackage] = {}
        for pkg_data in tour_packages_payload:
            pkg = _ensure_tour_package(owner_profile, pkg_data)
            tour_package_map[pkg_data["name"]] = pkg
        print(f"  Tour packages: {TourPackage.query.count()}")

        # ── Emergency Contacts ───────────────────────────────────────────────────
        print("Seeding emergency contacts...")
        emergency_contacts_payload = [
            # Nairobi
            {"destination_slug": "nairobi", "name": "Nairobi Police Station — Central", "type": "police", "phone": "+254-20-2222222", "street": "University Way", "city": "Nairobi", "region": "Nairobi County"},
            {"destination_slug": "nairobi", "name": "Kenyatta National Hospital", "type": "hospital", "phone": "+254-20-2726300", "street": "Hospital Rd, Upper Hill", "city": "Nairobi", "region": "Nairobi County"},
            {"destination_slug": "nairobi", "name": "Nairobi Fire Brigade", "type": "fire", "phone": "+254-20-2222181", "street": "Desai Rd", "city": "Nairobi", "region": "Nairobi County"},
            {"destination_slug": "nairobi", "name": "Kenya Wildlife Service — Nairobi HQ", "type": "wildlife_authority", "phone": "+254-20-6000800", "street": "Langata Rd", "city": "Nairobi", "region": "Nairobi County"},
            {"destination_slug": "nairobi", "name": "Kenya Red Cross — Nairobi", "type": "emergency", "phone": "+254-703-037000", "street": "Nairobi South", "city": "Nairobi", "region": "Nairobi County"},
            # Mombasa
            {"destination_slug": "mombasa", "name": "Mombasa Police Station", "type": "police", "phone": "+254-41-2311001", "street": "Baluchi St", "city": "Mombasa", "region": "Mombasa County"},
            {"destination_slug": "mombasa", "name": "Coast General Hospital", "type": "hospital", "phone": "+254-41-2314201", "street": "Baraza Rd", "city": "Mombasa", "region": "Mombasa County"},
            {"destination_slug": "mombasa", "name": "Mombasa Fire & Rescue", "type": "fire", "phone": "+254-41-2311111", "street": "Mwembe Tayari Rd", "city": "Mombasa", "region": "Mombasa County"},
            # Maasai Mara
            {"destination_slug": "maasai-mara", "name": "Narok Police Station", "type": "police", "phone": "+254-50-2022068", "street": "Narok Town", "city": "Narok", "region": "Narok County"},
            {"destination_slug": "maasai-mara", "name": "Narok County Referral Hospital", "type": "hospital", "phone": "+254-50-2022040", "street": "Hospital Rd, Narok", "city": "Narok", "region": "Narok County"},
            {"destination_slug": "maasai-mara", "name": "KWS Maasai Mara Ranger Post", "type": "wildlife_authority", "phone": "+254-713-020000", "street": "Sekenani Gate", "city": "Narok", "region": "Narok County"},
            # Naivasha
            {"destination_slug": "naivasha", "name": "Naivasha Police Station", "type": "police", "phone": "+254-50-2021101", "street": "Government Rd", "city": "Naivasha", "region": "Nakuru County"},
            {"destination_slug": "naivasha", "name": "Naivasha District Hospital", "type": "hospital", "phone": "+254-50-2020097", "street": "Hospital Rd", "city": "Naivasha", "region": "Nakuru County"},
            # Amboseli
            {"destination_slug": "amboseli", "name": "Loitokitok Police Station", "type": "police", "phone": "+254-45-622010", "street": "Loitokitok Town", "city": "Loitokitok", "region": "Kajiado County"},
            {"destination_slug": "amboseli", "name": "KWS Amboseli Ranger Post", "type": "wildlife_authority", "phone": "+254-45-622350", "street": "Amboseli Park Gate", "city": "Loitokitok", "region": "Kajiado County"},
        ]

        for contact_data in emergency_contacts_payload:
            destination = destination_map[contact_data["destination_slug"]]
            _ensure_emergency_contact(
                destination,
                contact_data["name"],
                {k: v for k, v in contact_data.items() if k not in ("destination_slug", "name")},
            )
        print(f"  Emergency contacts: {EmergencyContact.query.count()}")

        # ── Bookings ─────────────────────────────────────────────────────────────
        print("Seeding bookings...")

        nairobi_safari_acc = accommodation_map.get("Nairobi Safari Club Hotel")
        diani_acc = accommodation_map.get("Diani Reef Beach Resort & Spa")
        mara_acc = accommodation_map.get("Mara Serena Safari Lodge")
        naivasha_acc = accommodation_map.get("Lake Naivasha Sopa Resort")

        first_schedule = schedule_map.get("sched_0")
        mara_pkg = tour_package_map.get("Mara Migration Safari — 5 Days")
        naivasha_park = attraction_map.get("Hell's Gate National Park")

        if nairobi_safari_acc:
            nairobi_room = RoomType.query.filter_by(
                accommodation_id=nairobi_safari_acc.id, name="Deluxe City View Room"
            ).first()
            _ensure_booking(
                tourist_user,
                {
                    "reference_number": "BK-2024-00001",
                    "type": BookingType.HOTEL,
                    "status": BookingStatus.CONFIRMED,
                    "total_cost": 360.0,
                    "refund_status": RefundStatus.NONE,
                    "kiosk_id": kiosk_map.get("JKIA Terminal 1 Kiosk", kiosk_map.get("Nairobi SGR Station Kiosk")).id
                    if kiosk_map else None,
                },
                [
                    {
                        "target_type": BookingItemTargetType.ACCOMMODATION,
                        "target_id": nairobi_safari_acc.id,
                        "quantity": 2,
                        "price_at_booking": 180.0,
                        "notes": "2 nights, Deluxe City View Room",
                    }
                ],
            )

        if first_schedule:
            _ensure_booking(
                tourist_user,
                {
                    "reference_number": "BK-2024-00002",
                    "type": BookingType.TRANSPORT,
                    "status": BookingStatus.COMPLETED,
                    "total_cost": 1200.0,
                    "refund_status": RefundStatus.NONE,
                },
                [
                    {
                        "target_type": BookingItemTargetType.TRANSPORT,
                        "target_id": first_schedule.id,
                        "quantity": 1,
                        "price_at_booking": 1200.0,
                        "notes": "Nairobi to Mombasa SGR — Economy class",
                    }
                ],
            )

        if naivasha_park:
            _ensure_booking(
                tourist_user,
                {
                    "reference_number": "BK-2024-00003",
                    "type": BookingType.ACTIVITY,
                    "status": BookingStatus.PENDING,
                    "total_cost": 60.0,
                    "refund_status": RefundStatus.NONE,
                },
                [
                    {
                        "target_type": BookingItemTargetType.ATTRACTION,
                        "target_id": naivasha_park.id,
                        "quantity": 2,
                        "price_at_booking": 30.0,
                        "notes": "2 persons — entry ticket",
                    }
                ],
            )

        if mara_pkg:
            _ensure_booking(
                tourist_user,
                {
                    "reference_number": "BK-2024-00004",
                    "type": BookingType.TOUR,
                    "status": BookingStatus.CONFIRMED,
                    "total_cost": 3700.0,
                    "refund_status": RefundStatus.NONE,
                },
                [
                    {
                        "target_type": BookingItemTargetType.TOUR_PACKAGE,
                        "target_id": mara_pkg.id,
                        "quantity": 2,
                        "price_at_booking": 1850.0,
                        "notes": "2 participants — full board",
                    }
                ],
            )

        if diani_acc:
            _ensure_booking(
                tourist_user,
                {
                    "reference_number": "BK-2024-00005",
                    "type": BookingType.HOTEL,
                    "status": BookingStatus.CANCELLED,
                    "total_cost": 1440.0,
                    "refund_status": RefundStatus.PROCESSED,
                    "cancelled_at": datetime.utcnow() - timedelta(days=5),
                    "cancellation_reason": "Change of travel plans",
                },
                [
                    {
                        "target_type": BookingItemTargetType.ACCOMMODATION,
                        "target_id": diani_acc.id,
                        "quantity": 3,
                        "price_at_booking": 480.0,
                        "notes": "3 nights, Beach Front Suite",
                    }
                ],
            )

        if naivasha_acc:
            _ensure_booking(
                owner_user,
                {
                    "reference_number": "BK-2024-00006",
                    "type": BookingType.HOTEL,
                    "status": BookingStatus.COMPLETED,
                    "total_cost": 420.0,
                    "refund_status": RefundStatus.NONE,
                },
                [
                    {
                        "target_type": BookingItemTargetType.ACCOMMODATION,
                        "target_id": naivasha_acc.id,
                        "quantity": 3,
                        "price_at_booking": 140.0,
                        "notes": "3 nights, Lake View Cottage",
                    }
                ],
            )

        print(f"  Bookings: {Booking.query.count()}")

        # ── Commit all ───────────────────────────────────────────────────────────
        db.session.commit()

        print("\n✓ Kenyan seed data complete.")
        print(f"  Users          : {User.query.count()}")
        print(f"  Destinations   : {Destination.query.count()}")
        print(f"  Attractions    : {Attraction.query.count()}")
        print(f"  Accommodations : {Accommodation.query.count()}")
        print(f"  Room types     : {RoomType.query.count()}")
        print(f"  Events         : {Event.query.count()}")
        print(f"  Amenities      : {Amenity.query.count()}")
        print(f"  Stations       : {transport_station.query.count()}")
        print(f"  Transport routes : {TransportRoute.query.count()}")
        print(f"  Schedules      : {transport_schedule.query.count()}")
        print(f"  Kiosks         : {Kiosk.query.count()}")
        print(f"  Tour packages  : {TourPackage.query.count()}")
        print(f"  Emergency ctcts: {EmergencyContact.query.count()}")
        print(f"  Bookings       : {Booking.query.count()}")
        print(f"  Product profiles: {TourismProductProfile.query.count()}")
        print(f"\n  Tourist login  : tourist@example.com / Tourist123!")
        print(f"  Admin login    : admin@example.com / Admin1234!")
        print(f"  Owner login    : kenya.operator@example.com / password123")


if __name__ == "__main__":
    seed_data()
