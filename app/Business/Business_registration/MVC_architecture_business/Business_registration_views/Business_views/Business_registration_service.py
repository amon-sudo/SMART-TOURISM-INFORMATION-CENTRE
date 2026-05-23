from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from app.extensions import db

from ....utils.utilities import send_notification, paginate_query
from ...Business_registration_models.Business_registration_domain.Business_registration_domain import BusinessRegistrationRequest
from ...Business_registration_models.Business_repo.Business_registration_repo import BusinessRegistrationRepository


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class BusinessServiceError(Exception):
    """Base exception for business registration service errors."""


class RegistrationNotFoundError(BusinessServiceError):
    """Raised when a registration request cannot be found."""


class InvalidStatusTransitionError(BusinessServiceError):
    """Raised when an invalid status transition is attempted."""


_registration_repository = BusinessRegistrationRepository()


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def register_business_request(user_id: uuid.UUID, data: dict) -> BusinessRegistrationRequest:
    """
    Create and persist a new business registration request.

    A user may submit multiple registration requests over time.
    """
    reg_request = BusinessRegistrationRequest(
        user_id=user_id,
        **data,
    )
    db.session.add(reg_request)
    db.session.commit()
    db.session.refresh(reg_request)
    return reg_request


def get_registration_request(request_id: uuid.UUID) -> BusinessRegistrationRequest:
    """
    Fetch a single registration request by primary key.

    Raises:
        RegistrationNotFoundError
    """
    reg_request = db.session.get(BusinessRegistrationRequest, request_id)
    if reg_request is None:
        raise RegistrationNotFoundError(
            f"Registration request {request_id} not found."
        )
    return reg_request


def list_registration_requests(
    status: Optional[str] = None,
    search_query: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """
    Return a paginated list of registration requests.

    Returns a dict with keys: items, page, per_page, total, total_pages.
    """
    query = select(BusinessRegistrationRequest).order_by(
        BusinessRegistrationRequest.created_at.desc()
    )
    if status:
        query = query.where(BusinessRegistrationRequest.status == status)

    if search_query:
        query = query.where(
            BusinessRegistrationRequest.business_name.ilike(f"%{search_query}%")
        )

    return paginate_query(query, page=page, per_page=per_page)


def update_registration_request(
    request_id: uuid.UUID,
    user_id: uuid.UUID,
    data: dict,
) -> BusinessRegistrationRequest:
    """
    Allow the applicant to update a *rejected* request and resubmit it.

    Raises:
        RegistrationNotFoundError
        InvalidStatusTransitionError – if current status is not 'rejected'
    """
    reg_request = get_registration_request(request_id)

    if str(reg_request.user_id) != str(user_id):
        raise RegistrationNotFoundError(
            f"Registration request {request_id} not found."
        )

    if reg_request.status != "rejected":
        raise InvalidStatusTransitionError(
            "Only rejected requests can be updated and resubmitted."
        )

    updatable_fields = ("business_name", "business_type", "registration_doc")
    for field in updatable_fields:
        if field in data:
            setattr(reg_request, field, data[field])

    reg_request.status = "pending"
    reg_request.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    db.session.refresh(reg_request)
    return reg_request


def action_registration_request(
    request_id: uuid.UUID,
    admin_id: uuid.UUID,
    action_data: dict,
) -> BusinessRegistrationRequest:
    """
    Approve, reject, or suspend a registration request.

    On approval, automatically creates (or verifies) the BusinessProfile so
    all submitted data (address, phone, email, description) lands in the DB.

    Raises:
        RegistrationNotFoundError
        InvalidStatusTransitionError
    """
    reg_request = get_registration_request(request_id)

    new_status = action_data["status"]
    valid_transitions = {
        "pending": ("approved", "rejected", "suspended"),
        "rejected": ("pending",),
        "suspended": ("approved", "rejected"),
    }
    allowed = valid_transitions.get(reg_request.status, ())
    if new_status not in allowed:
        raise InvalidStatusTransitionError(
            f"Cannot transition from '{reg_request.status}' to '{new_status}'."
        )

    reg_request.status = new_status
    reg_request.reviewed_by = admin_id
    reg_request.reviewed_at = datetime.now(timezone.utc)
    reg_request.updated_at = datetime.now(timezone.utc)
    if action_data.get("rejection_reason"):
        reg_request.rejection_reason = action_data["rejection_reason"]
    db.session.commit()
    db.session.refresh(reg_request)

    if new_status == "approved":
        _provision_business_profile(reg_request)

    # Notify the applicant
    send_notification(
        user_id=reg_request.user_id,
        message=f"Your business registration request status has been updated to '{new_status}'.",
        notification_type="info",
    )

    return reg_request


def _provision_business_profile(reg_request: BusinessRegistrationRequest) -> None:
    """
    Create or update the BusinessProfile for an approved registration.

    Extracts the contact/location details stored in registration_doc and
    writes them to proper columns on BusinessProfile so the business is
    immediately queryable and can appear on the explore page once it has
    attractions linked to it.
    """
    from app.Business.Business_Profile.MVC_architecture.Business_profile_models.Business_profile_domain.Business_profile_domain import BusinessProfile

    existing = db.session.scalar(
        select(BusinessProfile).where(BusinessProfile.user_id == reg_request.user_id)
    )

    doc = reg_request.registration_doc or {}

    if existing is not None:
        existing.verified = True
        existing.is_active = True
        if existing.registration_request_id is None:
            existing.registration_request_id = reg_request.id
        # Fill in any missing fields from the registration doc
        for attr, key in (
            ("business_name", None),
            ("business_type", None),
            ("description", "description"),
            ("address", "address"),
            ("phone", "phone"),
            ("email", "email"),
        ):
            src = getattr(reg_request, attr, None) if key is None else doc.get(key)
            if src and not getattr(existing, attr):
                setattr(existing, attr, src)
        existing.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return

    profile = BusinessProfile(
        user_id=reg_request.user_id,
        registration_request_id=reg_request.id,
        business_name=reg_request.business_name,
        business_type=reg_request.business_type,
        description=doc.get("description"),
        address=doc.get("address"),
        phone=doc.get("phone"),
        email=doc.get("email"),
        verified=True,
        is_active=True,
    )
    db.session.add(profile)
    db.session.commit()


def delete_registration_request(
    request_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """
    Delete a user's own pending registration request.

    Raises:
        RegistrationNotFoundError
        InvalidStatusTransitionError
    """
    deleted, reason = _registration_repository.delete_own_pending_registration_request(
        request_id=request_id,
        user_id=user_id,
    )

    if deleted:
        return

    if reason == "not_found":
        raise RegistrationNotFoundError(
            f"Registration request {request_id} not found."
        )

    if reason == "invalid_status":
        raise InvalidStatusTransitionError(
            "Only pending requests can be deleted."
        )

    raise BusinessServiceError("Unable to delete registration request.")