
import uuid
from app.extensions import db
from datetime import datetime,timezone


class BusinessRegistrationRequest(db.Model):
	__tablename__ = "business_registration_requests"

	id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
	user_id = db.Column(
		db.Uuid(as_uuid=True),
		db.ForeignKey("users.id"),
		nullable=False,
		index=True,
	)
	business_name = db.Column(db.String(255), nullable=False)
	business_type = db.Column(db.String(100), nullable=False)
	registration_doc = db.Column(db.JSON, nullable=True, default = dict)
	status = db.Column(db.String(50), nullable=False, default="pending")
	reviewed_by = db.Column(
		db.Uuid(as_uuid=True),
		db.ForeignKey("users.id"),
		nullable=True,
	)
	reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
	
	created_at = db.Column(
		db.DateTime(timezone=True),
		nullable=False,
		server_default=db.func.now(),
	)
	updated_at = db.Column(
		db.DateTime(timezone=True),
		nullable=False,
		server_default=db.func.now(),
		onupdate=db.func.now(),
	)


# Relationships
user = db.relationship(
    "User",
    foreign_keys=[BusinessRegistrationRequest.user_id],
    back_populates="registration_requests",
)

reviewer = db.relationship(
    "User",
    foreign_keys=[BusinessRegistrationRequest.reviewed_by],
    back_populates="reviewed_registrations",
)

business_profile = db.relationship(
    "BusinessProfile",
    back_populates="registration_request",
    uselist=False,
)

