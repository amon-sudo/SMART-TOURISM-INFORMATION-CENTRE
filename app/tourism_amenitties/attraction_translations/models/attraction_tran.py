import uuid
from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID


class AttractionTranslation(db.Model):
    __tablename__ = "attraction_translations"

    attraction_id = db.Column(
        UUID(as_uuid=True),
        # db.ForeignKey("attractions.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )

    locale = db.Column(db.String(10), primary_key=True, nullable=False)

    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=False)
    tips = db.Column(db.Text)