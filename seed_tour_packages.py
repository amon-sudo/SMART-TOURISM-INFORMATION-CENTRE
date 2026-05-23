"""Minimal seeder — creates a business profile (if none exists) then seeds tour packages."""
from app import create_app
from app.extensions import db

app = create_app()

from app.user_settings.models.models import User  # noqa: E402
from app.Business.Business_Profile.MVC_architecture.Business_profile_models.Business_profile_domain.Business_profile_domain import BusinessProfile  # noqa: E402
from app.tourism_amenitties.tours.models.tour_package import TourPackage  # noqa: E402


PACKAGES = [
    {
        "name": "Mara Migration Safari — 5 Days",
        "description": "Experience the greatest wildlife spectacle on Earth. This 5-day package includes full-board accommodation at Mara Serena Lodge, twice-daily game drives, and a Maasai village cultural visit.",
        "duration_days": 5,
        "price": 1850.0,
        "max_participants": 8,
    },
    {
        "name": "Nairobi & Naivasha Weekend — 3 Days",
        "description": "Perfect weekend escape combining Nairobi National Park morning game drive, Lake Naivasha boat safari, and Hell's Gate cycling — all from Nairobi.",
        "duration_days": 3,
        "price": 480.0,
        "max_participants": 12,
    },
    {
        "name": "Kenya Coastal Escape — 7 Days",
        "description": "7-day luxury coastal package: Fort Jesus history tour, Diani Beach snorkelling, dhow cruise, and Wasini Island dolphin watching. Full board at Diani Reef Resort.",
        "duration_days": 7,
        "price": 2200.0,
        "max_participants": 10,
    },
    {
        "name": "Amboseli Elephant Safari — 4 Days",
        "description": "Marvel at Kilimanjaro and Africa's largest free-ranging elephant herds. 4 days full board at Amboseli Serena Lodge with expert naturalist guides.",
        "duration_days": 4,
        "price": 1400.0,
        "max_participants": 6,
    },
    {
        "name": "Kenya Grand Circuit — 10 Days",
        "description": "The ultimate Kenya experience: Nairobi, Amboseli, Maasai Mara, Lake Nakuru, and Mombasa. Luxury lodges throughout, all transfers included.",
        "duration_days": 10,
        "price": 4500.0,
        "max_participants": 8,
    },
    {
        "name": "Nairobi City & Culture Day Tour — 1 Day",
        "description": "A full-day Nairobi city tour: Nairobi National Park morning game drive, Karen Blixen Museum, Giraffe Centre, and Kazuri Beads factory. Ideal for layovers and city visitors.",
        "duration_days": 1,
        "price": 120.0,
        "max_participants": 15,
    },
    {
        "name": "Rift Valley Lakes Safari — 3 Days",
        "description": "Explore Lake Nakuru's flamingos, rhinos, and pelicans, then head to Lake Elementaita for sunrise birdwatching. Mid-range lodge accommodation included.",
        "duration_days": 3,
        "price": 650.0,
        "max_participants": 10,
    },
    {
        "name": "Mount Kenya Hiking Adventure — 6 Days",
        "description": "Summit Mount Kenya via the Sirimon–Chogoria route with certified mountain guides. Includes all park fees, camping gear, full-board, and porter support.",
        "duration_days": 6,
        "price": 980.0,
        "max_participants": 8,
    },
]


def seed():
    with app.app_context():
        # Get or create an operator user
        operator = User.query.filter_by(email="kenya.operator@example.com").first()
        if not operator:
            operator = User(email="kenya.operator@example.com", username="safarihorizons")
            operator.set_password("password123")
            db.session.add(operator)
            db.session.flush()
            print("Created operator user: kenya.operator@example.com / password123")

        # Get or create a business profile for that user
        bp = BusinessProfile.query.filter_by(user_id=operator.id).first()
        if not bp:
            bp = BusinessProfile(
                user_id=operator.id,
                business_name="Safari Horizons Kenya",
                business_type="tourism_operator",
                verified=True,
                is_active=True,
            )
            db.session.add(bp)
            db.session.flush()
            print(f"Created business profile: {bp.business_name}")

        # Seed tour packages (idempotent)
        created = 0
        updated = 0
        for data in PACKAGES:
            pkg = TourPackage.query.filter_by(name=data["name"], operator_id=bp.id).first()
            if pkg:
                pkg.description = data["description"]
                pkg.duration_days = data["duration_days"]
                pkg.price = data["price"]
                pkg.max_participants = data["max_participants"]
                pkg.status = "active"
                updated += 1
            else:
                pkg = TourPackage(
                    operator_id=bp.id,
                    name=data["name"],
                    description=data["description"],
                    duration_days=data["duration_days"],
                    price=data["price"],
                    max_participants=data["max_participants"],
                    status="active",
                )
                db.session.add(pkg)
                created += 1

        db.session.commit()
        total = TourPackage.query.count()
        print(f"\nDone. Created {created}, updated {updated}. Total tour packages: {total}")
        for p in TourPackage.query.order_by(TourPackage.price).all():
            print(f"  ${p.price:,.0f} — {p.name} ({p.duration_days}d, max {p.max_participants})")


if __name__ == "__main__":
    seed()
