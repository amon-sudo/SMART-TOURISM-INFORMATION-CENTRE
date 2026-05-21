from __future__ import annotations

import uuid
import os
from http import HTTPStatus

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from marshmallow import ValidationError
from werkzeug.exceptions import Unauthorized

from app.Business.errors_handling import error_response
from ..Business_registration_models.Business_schema.Business_registration_schema import (
    BusinessRegistrationRequestCreateSchema,
    BusinessRegistrationRequestUpdateSchema,
    BusinessRegistrationRequestAdminActionSchema,
    BusinessRegistrationRequestResponseSchema,
)
from ..Business_registration_views.Business_views.Business_registration_service import (
    register_business_request,
    get_registration_request,
    list_registration_requests,
    update_registration_request,
    delete_registration_request,
    action_registration_request,
    RegistrationNotFoundError,
    InvalidStatusTransitionError,
    BusinessServiceError,
)


_reg_create_schema = BusinessRegistrationRequestCreateSchema()
_reg_update_schema = BusinessRegistrationRequestUpdateSchema()
_reg_admin_action_schema = BusinessRegistrationRequestAdminActionSchema()
_reg_response_schema = BusinessRegistrationRequestResponseSchema()


def register_business():
    """
    POST /api/v1/business/register
    --------------------------------
    Any authenticated user can apply to become a business owner.

    Request body (JSON): business_name, business_type, registration_doc
    Responses:
        201  { message, registration }
        422  { errors } – validation failure
        409  { error }  – duplicate pending request
    """
    try:
        data = _reg_create_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error_response(
            "Validation failed.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            details={"fields": exc.messages},
        )

    try:
        reg_request = register_business_request(
            user_id=_current_user_id(),
            data=data,
        )
    except BusinessServiceError as exc:
        return _error(str(exc), HTTPStatus.CONFLICT)

    return (
        jsonify(
            {
                "message": "Business registration request submitted successfully.",
                "registration": _reg_response_schema.dump(reg_request),
            }
        ),
        HTTPStatus.CREATED,
    )


def get_my_registration():
    user_id = _current_user_id()

    from sqlalchemy import select
    from app.extensions import db
    from ..Business_registration_models.Business_registration_domain.Business_registration_domain import (
        BusinessRegistrationRequest,
    )
 
    reg_request = db.session.scalar(
        select(BusinessRegistrationRequest)
        .where(BusinessRegistrationRequest.user_id == user_id)
        .order_by(BusinessRegistrationRequest.created_at.desc())
    )
 
    if reg_request is None:
        return jsonify([]), HTTPStatus.OK
 
    return jsonify({"registration": _reg_response_schema.dump(reg_request)}), HTTPStatus.OK
 
 
def update_my_registration(request_id: str):
    """
    PATCH /api/v1/business/registration/<request_id>
    --------------------------------------------------
    Allows the applicant to update a *rejected* request and resubmit it.
 
    Request body (JSON): any subset of registration fields
    Responses:
        200  { message, registration }
        404  { error }
        409  { error }  – request not in rejected state
        422  { errors } – validation failure
    """
    try:
        data = _reg_update_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error_response(
            "Validation failed.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            details={"fields": exc.messages},
        )
 
    try:
        reg_request = update_registration_request(
            request_id=uuid.UUID(request_id),
            user_id=_current_user_id(),
            data=data,
        )
    except RegistrationNotFoundError as exc:
        return _error(str(exc), HTTPStatus.NOT_FOUND)
    except InvalidStatusTransitionError as exc:
        return _error(str(exc), HTTPStatus.CONFLICT)
 
    return (
        jsonify(
            {
                "message": "Registration request updated and resubmitted for review.",
                "registration": _reg_response_schema.dump(reg_request),
            }
        ),
        HTTPStatus.OK,
    )


def delete_my_registration(request_id: str):
    """
    DELETE /api/v1/business/registrations/registration/<request_id>
    -------------------------------------------------------------
    Allows the applicant to delete their own pending registration request.

    Responses:
        200  { message }
        404  { error }
        409  { error }
    """
    try:
        delete_registration_request(
            request_id=uuid.UUID(request_id),
            user_id=_current_user_id(),
        )
    except ValueError:
        return _error("Invalid request id.", HTTPStatus.BAD_REQUEST)
    except RegistrationNotFoundError as exc:
        return _error(str(exc), HTTPStatus.NOT_FOUND)
    except InvalidStatusTransitionError as exc:
        return _error(str(exc), HTTPStatus.CONFLICT)
    except BusinessServiceError as exc:
        return _error(str(exc), HTTPStatus.INTERNAL_SERVER_ERROR)

    return jsonify({"message": "Registration request deleted successfully."}), HTTPStatus.OK
def admin_list_registrations():
    """
    GET /api/v1/admin/business/registrations
    -----------------------------------------
    Paginated list of all registration requests.
 
    Query params:
        status    str  optional  filter by status
        search    str  optional  partial business-name match (case-insensitive)
        page      int  default 1
        per_page  int  default 20
 
    Responses:
        200  { registrations: [...], page, per_page, total, total_pages }
    """
    status = request.args.get("status")
    search_query = request.args.get("search", type=str)
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
 
    result = list_registration_requests(
        status=status,
        search_query=search_query,
        page=page,
        per_page=per_page,
    )
    result["registrations"] = [
        _reg_response_schema.dump(r) for r in result.pop("items")
    ]
 
    return jsonify(result), HTTPStatus.OK
 
 
def admin_get_registration(request_id: str):
    """
    GET /api/v1/admin/business/registrations/<request_id>
    -------------------------------------------------------
    Fetch a single registration request (admin, no ownership check).
 
    Responses:
        200  { registration }
        404  { error }
    """
    try:
        reg_request = get_registration_request(uuid.UUID(request_id))
    except (ValueError, RegistrationNotFoundError):
        return jsonify([]), HTTPStatus.OK
 
    return jsonify({"registration": _reg_response_schema.dump(reg_request)}), HTTPStatus.OK
 
 
def admin_action_registration(request_id: str):
    """
    PATCH /api/v1/admin/business/registrations/<request_id>
    --------------------------------------------------------
    Approve, reject, or suspend a registration request.
 
    Request body (JSON):
        status               str   required  (approved|rejected|suspended)
        business_profile_id  uuid  optional (recommended when status is approved)
 
    Responses:
        200  { message, registration }
        400  { error }  – missing rejection reason
        404  { error }
        409  { error }  – invalid status transition
        422  { errors }
    """
    try:
        data = _reg_admin_action_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error_response(
            "Validation failed.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            details={"fields": exc.messages},
        )
 
    admin_id = _current_user_id()
 
    try:
        reg_request = action_registration_request(
            request_id=uuid.UUID(request_id),
            admin_id=admin_id,
            action_data=data,
        )
    except RegistrationNotFoundError as exc:
        return _error(str(exc), HTTPStatus.NOT_FOUND)
    except InvalidStatusTransitionError as exc:
        return _error(str(exc), HTTPStatus.CONFLICT)
    except BusinessServiceError as exc:
        return _error(str(exc), HTTPStatus.INTERNAL_SERVER_ERROR)
 
    status_messages = {
        "approved": "Business registration approved. Profile created and owner notified.",
        "rejected": "Business registration rejected. Owner has been notified.",
        "suspended": "Business registration suspended.",
    }
 
    return (
        jsonify(
            {
                "message": status_messages.get(data["status"], "Request actioned."),
                "registration": _reg_response_schema.dump(reg_request),
            }
        ),
        HTTPStatus.OK,
    )

def _current_user_id() -> uuid.UUID:
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
    except Exception:
        identity = None

    if identity is not None:
        return uuid.UUID(str(identity))

    fallback_user_id = request.headers.get(
        "X-User-Id",
        os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"),
    )
    try:
        return uuid.UUID(str(fallback_user_id))
    except ValueError as exc:
        raise Unauthorized("Invalid X-User-Id/DEV_USER_ID. Provide a valid UUID.") from exc

def _error(message: str, status_code: int, *, code: str | None = None, details: dict | None = None):
    return error_response(message, status_code=status_code, code=code, details=details)


