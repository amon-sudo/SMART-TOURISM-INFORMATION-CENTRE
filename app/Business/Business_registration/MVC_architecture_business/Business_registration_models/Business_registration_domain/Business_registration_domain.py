import uuid

from app.extensions import db


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

	# One registration request creates at most one business profile.
	business_profile = db.relationship(
		"BusinessProfile",
		back_populates="registration_request",
		uselist=False,
	)

	# Owner-level one-to-many (same user can own multiple business profiles).
	owner_business_profiles = db.relationship(
		"BusinessProfile",
		primaryjoin="foreign(BusinessProfile.user_id) == BusinessRegistrationRequest.user_id",
		viewonly=True,
		lazy="selectin",
	)