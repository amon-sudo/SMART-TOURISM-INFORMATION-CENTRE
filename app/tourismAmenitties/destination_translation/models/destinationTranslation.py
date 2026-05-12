from extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB


class DestinationTranslation(db.Model):
    __tablename__ = "destination_translations"

    destination_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("destinations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )

    locale = db.Column(db.String(10), primary_key=True, nullable=False)

    name = db.Column(db.String, nullable=False)

    overview = db.Column(db.Text)

    culture = db.Column(db.Text)

    travel_tips = db.Column(db.Text)

    weather_info = db.Column(JSONB)