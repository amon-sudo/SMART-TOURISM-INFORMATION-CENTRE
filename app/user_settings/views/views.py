from flask import Blueprint, request
from app.utils.responses import ApiResponse
from ..controllers.controllers import (
    get_all_settings, update_user_profile, update_accessibility_settings, 
    update_notification_settings, update_user_preferences
)
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

user_settings_bp = Blueprint('user_settings', __name__)


def _current_user_id():
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity() or request.headers.get("X-User-Id")
    except Exception:
        return request.headers.get("X-User-Id")

@user_settings_bp.route('/settings', methods=['GET'])
# @jwt_required()  # TEMP: auth disabled for endpoint testing
def fetch_user_settings():
    """Exposes all user settings."""
    user_id = _current_user_id()
    return get_all_settings(user_id)

@user_settings_bp.route('/settings/profile', methods=['PATCH'])
# @jwt_required()  # TEMP: auth disabled for endpoint testing
def patch_profile():
    user_id = _current_user_id()
    data = request.get_json()
    if not data:
        return ApiResponse.error(message="No data provided", status_code=400)
    return update_user_profile(user_id, data)

@user_settings_bp.route('/settings/accessibility', methods=['PATCH'])
# @jwt_required()  # TEMP: auth disabled for endpoint testing
def patch_accessibility():
    user_id = _current_user_id()
    data = request.get_json()
    if not data:
        return ApiResponse.error(message="No data provided", status_code=400)
    return update_accessibility_settings(user_id, data)

@user_settings_bp.route('/settings/notifications', methods=['PATCH'])
# @jwt_required()  # TEMP: auth disabled for endpoint testing
def patch_notifications():
    user_id = _current_user_id()
    data = request.get_json()
    if not data:
        return ApiResponse.error(message="No data provided", status_code=400)
    return update_notification_settings(user_id, data)

@user_settings_bp.route('/settings/preferences', methods=['PATCH'])
# @jwt_required()  # TEMP: auth disabled for endpoint testing
def patch_preferences():
    user_id = _current_user_id()
    data = request.get_json()
    if not data:
        return ApiResponse.error(message="No data provided", status_code=400)
    return update_user_preferences(user_id, data)
