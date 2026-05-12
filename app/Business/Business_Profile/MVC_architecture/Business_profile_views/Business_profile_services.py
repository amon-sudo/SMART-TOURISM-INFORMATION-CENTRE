from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from app.extensions import db
from ..Business_profile_models.Business_profile_domain.Business_profile_domain import BusinessProfile


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class ProfileNotFoundError(Exception):
    """Raised when a business profile cannot be found."""


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def create_business_profile(user_id: uuid.UUID, data: dict) -> BusinessProfile:
    """
    Create a business profile for the given user.

    Typically called internally when a registration request is approved.
    """
    profile = BusinessProfile(user_id=user_id, **data)
    db.session.add(profile)
    db.session.commit()
    db.session.refresh(profile)
    return profile


def get_business_profile(user_id: uuid.UUID) -> BusinessProfile:
    """
    Fetch the business profile belonging to the given user.

    Raises:
        ProfileNotFoundError
    """
    profile = db.session.scalar(
        select(BusinessProfile)
        .where(
            BusinessProfile.user_id == user_id,
            BusinessProfile.is_active == True,
        )
        .order_by(BusinessProfile.created_at.desc())
    )
    if profile is None:
        raise ProfileNotFoundError(
            f"No business profile found for user {user_id}."
        )
    return profile


def list_user_business_profiles(user_id: uuid.UUID):
    """Return all active business profiles for a given owner."""
    result = db.session.execute(
        select(BusinessProfile)
        .where(
            BusinessProfile.user_id == user_id,
            BusinessProfile.is_active == True,
        )
        .order_by(BusinessProfile.created_at.desc())
    )
    return result.scalars().all()


def get_business_profile_by_id(
    profile_id: uuid.UUID,
    public: bool = True,
) -> BusinessProfile:
    """
    Fetch a business profile by its own UUID.

    Args:
        profile_id : UUID of the BusinessProfile record.
        public     : When True only active+verified profiles are returned
                     (public endpoint). Pass False for admin access.

    Raises:
        ProfileNotFoundError
    """
    query = select(BusinessProfile).where(BusinessProfile.id == profile_id)
    if public:
        query = query.where(
            BusinessProfile.is_active == True,
            BusinessProfile.verified == True,
        )

    profile = db.session.scalar(query)
    if profile is None:
        raise ProfileNotFoundError(f"Business profile {profile_id} not found.")
    return profile


def get_all_business_profiles(
    public: bool = False,
    search_query: Optional[str] = None,
):
    """Return all business profiles, optionally filtered to active+verified."""
    query = select(BusinessProfile).order_by(BusinessProfile.created_at.desc())
    if public:
        query = query.where(
            BusinessProfile.is_active == True,
            BusinessProfile.verified == True,
        )
    if search_query:
        query = query.where(BusinessProfile.business_name.ilike(f"%{search_query}%"))
    result = db.session.execute(query)
    return result.scalars().all()


def update_business_profile(
    user_id: uuid.UUID,
    data: dict,
    profile_id: Optional[uuid.UUID] = None,
) -> BusinessProfile:
    """
    Update the business profile for the given user.

    Raises:
        ProfileNotFoundError
    """
    profile = (
        get_business_profile_by_id(profile_id, public=False)
        if profile_id is not None
        else get_business_profile(user_id)
    )

    if str(profile.user_id) != str(user_id):
        raise ProfileNotFoundError(f"Business profile {profile.id} not found.")

    updatable_fields = (
        "phone", "email", "address", "description",
        "business_name", "business_type",
    )

    for field in updatable_fields:
        if field in data and data[field] is not None:
            setattr(profile, field, data[field])

    profile.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    db.session.refresh(profile)
    return profile


def delete_business_profile(user_id: uuid.UUID, profile_id: uuid.UUID) -> bool:
    """
    Soft-delete (deactivate) a business profile.

    Raises:
        ProfileNotFoundError
    """
    profile = get_business_profile_by_id(profile_id, public=False)
    if str(profile.user_id) != str(user_id):
        raise ProfileNotFoundError(f"Business profile {profile_id} not found.")
    profile.is_active = False
    profile.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return True
 